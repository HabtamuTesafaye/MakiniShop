pipeline {
    agent any

    environment {
        SERVICE_NAME = "web"
        DOCKER_IMAGE = "makinishop:latest"
        VERSION_TAG = "yourdockerhubusername/makinishop:${env.BUILD_NUMBER}"
        DOCKER_COMPOSE_FILE = "docker-compose.yml"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Cloning source code..."
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                sh "docker-compose -f ${DOCKER_COMPOSE_FILE} build ${SERVICE_NAME}"
                // Tag the image immediately for testing
                sh "docker tag ${DOCKER_IMAGE} ${VERSION_TAG}"
            }
        }

        stage('Run Tests') {
            steps {
                echo "Running tests inside the built Docker image..."
                // Inject credentials securely
                withCredentials([
                    string(credentialsId: 'pg_db', variable: 'POSTGRES_DB'),
                    string(credentialsId: 'pg_user', variable: 'POSTGRES_USER'),
                    string(credentialsId: 'pg_pass', variable: 'POSTGRES_PASSWORD'),
                    string(credentialsId: 'rabbitmq_user', variable: 'RABBITMQ_USER'),
                    string(credentialsId: 'rabbitmq_pass', variable: 'RABBITMQ_PASSWORD'),
                    string(credentialsId: 'django_secret_key', variable: 'DJANGO_SECRET_KEY')
                ]) {
                    script {
                        // Export env vars for docker-compose
                        def envVars = [
                            "POSTGRES_DB=${POSTGRES_DB}",
                            "POSTGRES_USER=${POSTGRES_USER}",
                            "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}",
                            "RABBITMQ_USER=${RABBITMQ_USER}",
                            "RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}",
                            "DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}"
                        ].join(" ")

                        // Start dependent services
                        sh "docker-compose -f ${DOCKER_COMPOSE_FILE} up -d postgres rabbitmq redis"
                        // Wait for services to be ready
                        sh "sleep 15"

                        // Run migrations and tests inside the built image
                        sh "docker run --rm ${VERSION_TAG} /bin/sh -c 'python manage.py migrate && python manage.py test'"
                    }
                }
            }
        }

        stage('Push Docker Image') {
            when { branch 'main' }
            steps {
                echo "Pushing Docker image to registry..."
                sh "docker push ${VERSION_TAG}"
                sh "docker tag ${DOCKER_IMAGE} yourdockerhubusername/makinishop:latest"
                sh "docker push yourdockerhubusername/makinishop:latest"
            }
        }

        stage('Deploy') {
            when { branch 'main' }
            steps {
                echo "Deploying latest image..."
                // Use the pre-built image; no rebuild
                sh "docker-compose -f ${DOCKER_COMPOSE_FILE} up -d --no-build --no-deps ${SERVICE_NAME}"
            }
        }
    }

    post {
        always {
            echo "Cleaning up test containers..."
            sh "docker-compose -f ${DOCKER_COMPOSE_FILE} down --remove-orphans postgres rabbitmq redis"
        }
    }
}
