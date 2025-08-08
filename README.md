# Django E-Commerce Platform
![Django](https://img.shields.io/badge/Django-3.2-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![REST](https://img.shields.io/badge/REST_API-Yes-yellow)
![Swagger](https://img.shields.io/badge/Swagger-UI-supported-brightgreen)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Celery](https://img.shields.io/badge/Celery-RabbitMQ-green)



## 📋 Table of Contents
1. [Features Overview](#-features-overview)
2. [API Documentation](#-api-documentation)
   - [Authentication](#authentication)
   - [Products](#products)
   - [Cart](#cart)
   - [Orders](#orders)
3. [Swagger Usage](#swagger-usage)
4. [Docker Containerization](#docker-containerization)
5. [Celery & RabbitMQ](#celery--rabbitmq)
6. [Admin Guide](#-admin-guide)
7. [Installation](#-installation)
8. [Configuration](#configuration)
9. [Development Notes](#-development-notes)

A modular e-commerce platform built with Django, featuring product catalog, user management, cart functionality, order processing, and review system with advanced filtering capabilities.

## Overview

This Django-powered e-commerce backend provides scalable and modular functionality for managing an online store. The newly enhanced product APIs now support advanced filtering, pagination, and robust admin controls. The platform now includes comprehensive API documentation via Swagger UI.

New enhancements include:

- **Interactive Swagger UI** for API exploration & testing.
- **Dockerized deployment** for consistent environment and scalability.
- **Celery + RabbitMQ** for background task processing (emails, reports, payment confirmations).

---

## Swagger Usage

The platform uses **Swagger UI** (`drf-yasg`) for API documentation.

### Accessing Swagger
- Development: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
- ReDoc alternative: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)


## Features

### Core Functionality
- **Enhanced Product Catalog** with filtering/pagination
- Category organization
- User review system
- Shopping cart functionality
- Order processing system
- Admin dashboard with advanced controls



### 🔍 Advanced Product API Features
- **Filtering** by:
  - Price range (`min_price`, `max_price`)
  - Category (`category=electronics`)
  - Availability (`available=true`)
  - Search term (`search=laptop`)
- **Sorting** (`ordering=-price`, `ordering=created_at`)
- **Pagination** (10 items/page, customizable via `page_size`)

### Admin Interface Highlights
- **Category Management**:
  - Create/edit categories with automatic slug generation
  - View product counts per category
  - Inline product management

- **Product Management**:
  - Comprehensive product editing
  - Pricing and inventory control
  - Image uploads
  - Automatic slug generation

- **Order Management**:
  - View and process customer orders
  - Update order status
  - Filter orders by date/status

- **Review System**:
  - Review moderation
  - User rating management
  - Comment previews
  

### 🔐 Authentication & User Management (Accounts App)
- Custom `User` model with email-based login
- JWT authentication using `djangorestframework-simplejwt`
- User registration via API
- Secure password hashing
- Optional fields: profile photo, date of birth, created_by

### 📦 Product Management (Products App)
- Product model with:
  - Title
  - Description
  - Price
  - Inventory
  - Slug (for SEO-friendly URLs)
- Auto slug generation based on product title
- Product listing & detail views via API
- Admin support for CRUD

### 🛒 Cart Functionality (Cart App)
- Session-based cart system
- API endpoints for cart management
- Add/remove items
- Update quantities
- Clear cart

### 📦 Order Processing (Order App)
- Order creation from cart
- Multiple payment methods
- Order history for users
- Status tracking
- Admin management interface

### 📚 API Documentation (Swagger)
- Interactive API documentation
- Endpoint testing interface
- Schema definition
- Authentication support
- Available at `/swagger/` and `/redoc/`

---
### docker-compose.yml Example
```yaml
version: '3.9'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - rabbitmq

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"

  celery:
    build: .
    command: celery -A ecommerce worker -l info
    volumes:
      - .:/code
    depends_on:
      - db
      - rabbitmq
```

### Running the App
```bash
docker-compose up --build
```

### Celery & RabbitMQ
Celery is integrated for asynchronous tasks such as:

- Sending order confirmation emails.

- Processing payments.

- Generating weekly sales reports.

### Starting Celery Worker
```bash
celery -A ecommerce worker -l info
```

### Configuration
(Includes .env settings for DB, Celery broker, etc.)
# Celery & RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=rpc://
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=30

---
## 🛠️ Tech Stack

- **Backend:** Django & Django REST Framework
- **Authentication:** JWT via `simplejwt`
- **Database:** SQLite (default) / PostgreSQL-ready
- **Filtering:** Django Filter backend
- **Pagination:** Django REST Framework pagination
- **API Docs:** drf-yasg (Swagger/OpenAPI)
- **Language:** Python 3.11+
- **Environment Management:** `venv`

---

## 🧪 API Endpoints (WIP)

### Authentication
- `POST /api/auth/register/` – Register a new user
- `POST /api/auth/register/` – Register a new user
- `POST /api/token/` – Get access + refresh tokens
- `POST /api/token/refresh/` – Refresh access token

### Products
| Endpoint                      | Method | Description                      |
|-------------------------------|--------|----------------------------------|
| `/api/products/`              | GET    | List all products (filterable)   |
| `/api/products/`              | POST   | Create new product               |
| `/api/products/{slug}/`       | GET    | Product details                  |
| `/api/products/{slug}/`       | PUT    | Update product                   |
| `/api/products/{slug}/`       | DELETE | Remove product                   |
| `/api/products/{slug}/reviews/` | GET    | List product reviews             |
| `/api/products/{slug}/reviews/` | POST   | Add new review                   |

### Cart
| Endpoint            | Method | Description                     |
|---------------------|--------|---------------------------------|
| `/api/cart/`        | GET    | View cart contents              |
| `/api/cart/`        | POST   | Add item to cart                |
| `/api/cart/{id}/`   | PUT    | Update cart item quantity       |
| `/api/cart/{id}/`   | DELETE | Remove item from cart           |
| `/api/cart/clear/`  | POST   | Empty the cart                  |


### Orders
| Endpoint            | Method | Description                     |
|---------------------|--------|---------------------------------|
| `/api/orders/`      | GET    | List user's orders              |
| `/api/orders/`      | POST   | Create new order from cart      |
| `/api/orders/{id}/` | GET    | Order details                   |
| `/api/orders/{id}/` | PUT    | Update order status (admin)     |

### Documentation
| Endpoint       | Description                     |
|---------------|---------------------------------|
| `/swagger/`   | Interactive Swagger UI          |
| `/redoc/`     | Alternative documentation view  |

---

## Installation
### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip 20+

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/project-nexus.git
   cd project-nexus
   ```

 2. **Set up virtual environment**:
 ```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies**:
```
pip install -r requirements.txt
```

4. **Database setup**
```
python manage.py migrate
python manage.py createsuperuser
```

5. **Run development server**:
```
python manage.py runserver
```

---
### Configuration
1. **Environment variables**:
Create a `.env` file with:
```
    SECRET_KEY=your-secret-key-here
    DEBUG=True
    DB_NAME=djangocommerce
    DB_USER=postgres
    DB_PASSWORD=yourpassword
    DB_HOST=localhost
    DB_PORT=5432
```

2. **Media files**:
Add to settings.py:
- MEDIA_URL = '/media/'
- MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

## Admin Guide

### Accessing the Admin
- URL: `/admin/`  
- Use superuser credentials created during installation  

3. ### Key Admin Features

#### Categories
**Adding Categories**:
1. Navigate to Products → Categories  
2. Click "Add Category"  
3. Fill in name and description  
4. Slug auto-generates from name  
5. Save to create  

**Inline Products**:
- Add products directly when creating categories  
- Incomplete products are automatically filtered  

#### Products
**Product Fields**:
- Required: Name, Category, Price, Stock
- Optional: Description, Image
- Automatic: Created/Updated timestamps

#### Reviews
**Moderation**:
- Filter by rating
- Search by product or user
- View comment previews

### Cart
**Viewing Carts:**
- Browse active user carts
- See cart contents and totals
- Filter by user or creation date

### Orders
**Order Management:**
- View all orders
- Filter by status or date
- Update order status
- View order details

#### Development Notes

- Swagger UI is auto-generated — just ensure your endpoints are registered in urls.py.

- Docker environment replicates production setup.

- Celery tasks will not run without RabbitMQ running.

**Models Overview**
- Category: Product grouping with slug URLs

- Product: Core item with pricing/inventory

- Review: User feedback system

- Cart: Temporary storage for products

- CartItem: Individual cart entries

- Order: Completed purchases

- OrderItem: Products in orders

**Custom Admin Features**
- Product count per category

- Description/comment previews

- Smart form validation

- Organized field sets

- Order status tracking

#### Troubleshooting
**Common Issues**:

1. **Missing database columns**:
```
python manage.py makemigrations
python manage.py migrate
```

2. **Admin validation errors**:

- Ensure all required fields are complete

- Check model definitions match database

3. **Image uploads not working**:

- Verify MEDIA settings

- Check directory permissions

4. **Swagger not loading:**

- Check drf-yasg is in installed apps

- Verify URLs are properly configured

- Ensure DEBUG=True during development
