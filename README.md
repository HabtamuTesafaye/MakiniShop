# 🛍️ Makinishop Backend

**Makinishop** is a scalable, Django-based backend for an e-commerce platform. It supports product catalog management, personalized featured products, wishlists, and user reviews. It’s designed with performance, caching, and personalization in mind.

---

## 📦 Features

### Products & Categories

* **Category Management**: List all product categories.
* **Product Management**: List, filter, and retrieve products with detailed information.
* **Product Variants & Images**: Each product can have multiple images and variants.
* **Caching**: Product list responses are cached to reduce DB load.

### Featured Products

* **Standard Featured**: List products featured globally.
* **Personalized Featured**: User-specific featured products using wishlist data for prioritization.

### Wishlist

* Authenticated users can add/remove products to their wishlist.
* Users can list all wishlist items.

### Reviews

* Users can list and add reviews for products.
* Only review owners can update or delete their reviews.
* Public/private and anonymous review options.

### Admin Features

* CRUD endpoints for featured products.
* Full control over featured product scheduling and prioritization.

---

## 🛠️ Tech Stack

* **Backend**: Django, Django REST Framework (DRF)
* **Database**: PostgreSQL with advanced indexing (`GIN`, trigram for search)
* **Caching**: Django caching framework (supports Redis/other backends)
* **Authentication**: Django built-in user model, JWT/Token auth ready

---

## 📄 Models

* **Category**: `id`, `name`, `slug`, `description`
* **Product**: `id`, `sku`, `name`, `price`, `stock`, `is_active`, `category`, `metadata`
* **ProductImage**: `path`, `is_primary`, `width`, `height`
* **ProductVariant**: `sku`, `name`, `price`, `stock`, `metadata`
* **FeaturedProduct**: `product`, `start_date`, `end_date`, `priority`, `is_personalized`
* **Wishlist**: `user`, `product`
* **ProductReview**: `product`, `user`, `rating`, `comment`, `is_public`, `is_anonymous`

---

## 🔗 API Endpoints

### Categories

* `GET /categories/` → List all categories

### Products

* `GET /products/` → List products with filters: `category_id`, `min_price`, `max_price`, `q`
* `GET /products/<id>/` → Retrieve product details

### Product Reviews

* `GET /products/<product_id>/reviews/` → List reviews
* `POST /products/<product_id>/reviews/` → Add a review
* `PUT/PATCH /products/<product_id>/reviews/<id>/` → Update a review (owner only)
* `DELETE /products/<product_id>/reviews/<id>/` → Delete a review (owner only)

### Featured Products

* `GET /featured/` → List standard featured products
* `GET /featured/personalized/` → List personalized featured products

### Wishlist

* `GET /wishlist/` → List user wishlist
* `POST /wishlist/add/` → Add product to wishlist
* `DELETE /wishlist/<id>/delete/` → Remove product from wishlist

### Admin Featured Management

* `POST /admin/featured/` → Create featured product
* `PUT /admin/featured/<id>/` → Update featured product
* `DELETE /admin/featured/<id>/delete/` → Delete featured product

---

## ⚡ Caching & Performance

* Product lists are cached using query params as cache keys.
* Featured products prefetch related `images` and `variants` for fast retrieval.
* PostgreSQL indexes optimize category and price filtering and search.

---

## 🔐 Permissions

* **Reviews**: Authenticated users can create; only owners can update/delete.
* **Wishlist**: Authenticated users only.
* **Admin featured**: Restricted to admin users (use DRF permissions).

---

## 🏗️ Setup & Run

1. **Clone the repository**

```bash
git clone <repo-url>
cd makinishop
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Apply migrations**

```bash
python manage.py migrate
```

4. **Run the server**

```bash
python manage.py runserver
```

---

## 🔮 Future Improvements

* Full authentication with JWT
* Search endpoint with advanced filtering & sorting
* Product recommendation engine integration using embeddings
* Admin dashboard for featured products and analytics

---
