BEGIN;

-- ==========================================================
-- EXTENSIONS
-- ==========================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================================
-- ENUM TYPES
-- ==========================================================
CREATE TYPE order_status AS ENUM ('open', 'pending', 'paid', 'shipped', 'completed', 'cancelled');
CREATE TYPE cart_status AS ENUM ('open', 'abandoned');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');
CREATE TYPE discount_type AS ENUM ('percent', 'fixed', 'flash', 'bundle');
CREATE TYPE shipping_status AS ENUM ('pending', 'shipped', 'delivered', 'cancelled');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed');

-- ==========================================================
-- TRIGGER FUNCTION: updated_at
-- ==========================================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================================
-- ROLES & PERMISSIONS
-- ==========================================================
CREATE TABLE IF NOT EXISTS role (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_role_updated
BEFORE UPDATE ON role FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS permission (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS role_permission (
    role_id BIGINT REFERENCES role(id) ON DELETE CASCADE,
    permission_id BIGINT REFERENCES permission(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- ==========================================================
-- USERS
-- ==========================================================
CREATE TABLE IF NOT EXISTS user_account (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    email TEXT NOT NULL UNIQUE,
    phone TEXT UNIQUE,
    password TEXT NOT NULL,
    first_name TEXT DEFAULT '',
    last_name TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_user_email ON user_account (lower(email));
CREATE TRIGGER trg_user_account_updated
BEFORE UPDATE ON user_account FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS user_role (
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    role_id BIGINT REFERENCES role(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- ==========================================================
-- CATEGORY & PRODUCTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS category (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_category_updated
BEFORE UPDATE ON category FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS product (
    id BIGSERIAL PRIMARY KEY,
    sku TEXT UNIQUE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    price NUMERIC(12,2) NOT NULL DEFAULT 0,
    category_id BIGINT REFERENCES category(id) ON DELETE SET NULL,
    stock INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    avg_rating NUMERIC(3,2) DEFAULT 0,
    rating_count INT DEFAULT 0,
    review_count INT DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    purchase_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_product_category_active ON product(category_id, is_active);
CREATE INDEX IF NOT EXISTS idx_product_price ON product(price);
CREATE INDEX IF NOT EXISTS idx_product_name_trgm ON product USING gin(name gin_trgm_ops);
CREATE TRIGGER trg_product_updated
BEFORE UPDATE ON product FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Product Images
CREATE TABLE IF NOT EXISTS product_image (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    width INT,
    height INT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_product_image_product ON product_image(product_id);
CREATE TRIGGER trg_product_image_updated
BEFORE UPDATE ON product_image FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- WISHLIST
-- ==========================================================
CREATE TABLE IF NOT EXISTS wishlist (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, product_id)
);

CREATE OR REPLACE VIEW wishlist_with_details AS
SELECT w.id, w.user_id, p.id AS product_id, p.name, p.price,
       (SELECT path FROM product_image pi WHERE pi.product_id = p.id AND pi.is_primary = TRUE LIMIT 1) AS image_url
FROM wishlist w
JOIN product p ON w.product_id = p.id;

-- ==========================================================
-- PRODUCT VARIANTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS product_variant (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    sku TEXT,
    name TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL DEFAULT 0,
    stock INT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(product_id, sku)
);
CREATE TRIGGER trg_product_variant_updated
BEFORE UPDATE ON product_variant FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_variant_default
ON product_variant(product_id) WHERE sku IS NULL;

-- ==========================================================
-- CARTS & ORDERS
-- ==========================================================
CREATE TABLE IF NOT EXISTS cart (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    session_id UUID,
    status cart_status NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id);
CREATE TRIGGER trg_cart_updated
BEFORE UPDATE ON cart FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS cart_item (
    id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT REFERENCES cart(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES product(id) ON DELETE RESTRICT,
    variant_id BIGINT REFERENCES product_variant(id) ON DELETE RESTRICT,
    quantity INT NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL,
    total NUMERIC(12,2) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cart_item_cart ON cart_item(cart_id);
CREATE TRIGGER trg_cart_item_updated
BEFORE UPDATE ON cart_item FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- CUSTOMER ORDERS & ORDER ITEMS
-- ==========================================================
CREATE TABLE IF NOT EXISTS customer_order (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE SET NULL,
    status order_status NOT NULL DEFAULT 'pending',
    total NUMERIC(12,2) DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_customer_order_user ON customer_order(user_id);
CREATE TRIGGER trg_customer_order_updated
BEFORE UPDATE ON customer_order FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS order_item (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES customer_order(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES product(id) ON DELETE RESTRICT,
    unit_price NUMERIC(12,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    total NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_order_item_order_product ON order_item(order_id, product_id);
CREATE TRIGGER trg_order_item_updated
BEFORE UPDATE ON order_item FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- PAYMENTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS payment (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES customer_order(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    transaction_id TEXT UNIQUE,
    amount NUMERIC(12,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    status payment_status DEFAULT 'pending',
    paid_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_payment_order ON payment(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON payment(status);
CREATE TRIGGER trg_payment_updated
BEFORE UPDATE ON payment FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- DISCOUNTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS product_discount (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    code TEXT,
    type discount_type NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_product_discount_product ON product_discount(product_id);
CREATE INDEX IF NOT EXISTS idx_product_discount_active ON product_discount(product_id, active, starts_at, ends_at);
CREATE TRIGGER trg_product_discount_updated
BEFORE UPDATE ON product_discount FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS order_discount (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES customer_order(id) ON DELETE CASCADE,
    discount_id BIGINT REFERENCES product_discount(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_order_discount_order ON order_discount(order_id);
CREATE TRIGGER trg_order_discount_updated
BEFORE UPDATE ON order_discount FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- SHIPPING
-- ==========================================================
CREATE TABLE IF NOT EXISTS shipping_method (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT,
    min_cart_value NUMERIC(12,2) CHECK (min_cart_value >= 0),
    cost NUMERIC(12,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_shipping_method_updated
BEFORE UPDATE ON shipping_method FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS order_shipping (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT REFERENCES customer_order(id) ON DELETE CASCADE,
    shipping_method_id BIGINT REFERENCES shipping_method(id) ON DELETE SET NULL,
    cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    tracking_number TEXT,
    status shipping_status DEFAULT 'pending',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_order_shipping_order ON order_shipping(order_id);
CREATE TRIGGER trg_order_shipping_updated
BEFORE UPDATE ON order_shipping FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- WISHLIST
-- ==========================================================
CREATE TABLE IF NOT EXISTS wishlist (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, product_id)
);

CREATE OR REPLACE VIEW wishlist_with_details AS
SELECT w.id, w.user_id, p.id AS product_id, p.name, p.price,
       (SELECT path FROM product_image pi WHERE pi.product_id = p.id AND pi.is_primary = TRUE LIMIT 1) AS image_url
FROM wishlist w
JOIN product p ON w.product_id = p.id;

-- ==========================================================
-- PRODUCT RATINGS & REVIEWS
-- ==========================================================
CREATE TABLE IF NOT EXISTS product_rating (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_product_rating_product ON product_rating(product_id);
CREATE INDEX IF NOT EXISTS idx_product_rating_user ON product_rating(user_id);
CREATE TRIGGER trg_product_rating_updated
BEFORE UPDATE ON product_rating FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS product_review (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    title TEXT,
    body TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    is_anonymous BOOLEAN DEFAULT FALSE,
    rating SMALLINT CHECK (rating IS NULL OR (rating BETWEEN 1 AND 5)),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_product_review_product ON product_review(product_id);
CREATE INDEX IF NOT EXISTS idx_product_review_is_public ON product_review(product_id, is_public);
CREATE TRIGGER trg_product_review_updated
BEFORE UPDATE ON product_review FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- FEATURED PRODUCTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS featured_product (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    start_date TIMESTAMPTZ DEFAULT now(),
    end_date TIMESTAMPTZ,
    priority INT DEFAULT 0, -- higher = more prominent
    is_personalized BOOLEAN DEFAULT FALSE, -- admin flag to mark as personalized campaign
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(product_id, start_date) -- prevents duplicate active entries
);

CREATE INDEX IF NOT EXISTS idx_featured_product_active
    ON featured_product (start_date, end_date, priority);

CREATE TRIGGER trg_featured_product_updated
BEFORE UPDATE ON featured_product
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- USER EVENTS
-- ==========================================================
CREATE TABLE IF NOT EXISTS user_event (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    anon_id UUID,
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    value NUMERIC DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_user_event_user_created ON user_event(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_event_anon_created ON user_event(anon_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_event_product_created ON user_event(product_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_event_type_created ON user_event(event_type, created_at);

-- ==========================================================
-- AI / RECOMMENDATIONS
-- ==========================================================
CREATE TABLE IF NOT EXISTS product_embedding (
    product_id BIGINT PRIMARY KEY REFERENCES product(id) ON DELETE CASCADE,
    embedding vector(384),
    model TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_product_embedding_ivf ON product_embedding USING ivfflat(embedding) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS product_recommendation (
    product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    recommended_product_id BIGINT REFERENCES product(id) ON DELETE CASCADE,
    score DOUBLE PRECISION NOT NULL,
    rank INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY(product_id, recommended_product_id)
);
CREATE INDEX IF NOT EXISTS idx_product_reco_product_score ON product_recommendation(product_id, score DESC);

CREATE TABLE IF NOT EXISTS product_cooccurrence (
    product_a BIGINT REFERENCES product(id) ON DELETE CASCADE,
    product_b BIGINT REFERENCES product(id) ON DELETE CASCADE,
    count BIGINT DEFAULT 0,
    score DOUBLE PRECISION DEFAULT 0,
    last_seen TIMESTAMPTZ,
    PRIMARY KEY(product_a, product_b)
);
CREATE INDEX IF NOT EXISTS idx_cooccurrence_a ON product_cooccurrence(product_a);
CREATE INDEX IF NOT EXISTS idx_cooccurrence_b ON product_cooccurrence(product_b);

-- ==========================================================
-- NOTIFICATIONS
-- ==========================================================
CREATE TABLE IF NOT EXISTS notification_template (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notification_template_name ON notification_template(name);
CREATE TRIGGER trg_notification_template_updated
BEFORE UPDATE ON notification_template FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS user_notification_pref (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    event_type TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    frequency TEXT DEFAULT 'immediate',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, channel, event_type)
);
CREATE INDEX IF NOT EXISTS idx_user_notification_pref_user ON user_notification_pref(user_id);
CREATE TRIGGER trg_user_notification_pref_updated
BEFORE UPDATE ON user_notification_pref FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TABLE IF NOT EXISTS notification_queue (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE SET NULL,
    anon_id UUID,
    channel TEXT NOT NULL,
    template_id BIGINT REFERENCES notification_template(id),
    context JSONB DEFAULT '{}'::jsonb,
    priority INT DEFAULT 100,
    status notification_status DEFAULT 'pending',
    error TEXT,
    scheduled_at TIMESTAMPTZ DEFAULT now(),
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    last_attempt_at TIMESTAMPTZ,
    provider_message_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_notification_queue_status_sched ON notification_queue(status, scheduled_at);
CREATE TRIGGER trg_notification_queue_updated
BEFORE UPDATE ON notification_queue FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ==========================================================
-- AUDIT LOGS
-- ==========================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES user_account(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    object_type TEXT,
    object_id BIGINT,
    metadata JSONB DEFAULT '{}'::jsonb,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_created ON audit_log(user_id, created_at);

COMMIT;