# Shopping API Documentation

**Version:** 1.0.0

REST API for Shopping Application including Users, Products, Categories, Banners, Cart, Wishlist, Orders, Payments, Reviews, Ratings, Offers, Coupons and Product Management.

## Base URL

```text
http://127.0.0.1:5000
```

## Swagger Documentation

```text
http://127.0.0.1:5000/api/docs
```

## API Summary

**Total API endpoints:** 184

## Banners

### `/api/banners`

- **POST** — Create Banner Route
- **GET** — Get Banners Route

### `/api/banners/active`

- **GET** — Get Active Banners Route

### `/api/banners/featured`

- **GET** — Get Featured Banners Route

### `/api/banners/refresh-status`

- **POST** — Refresh Banner Status Route

### `/api/banners/search`

- **GET** — Search Banners Route

### `/api/banners/{banner_id}`

- **GET** — Get Banner By Id Route
- **PUT** — Update Banner Route
- **DELETE** — Delete Banner Route

### `/api/banners/{banner_id}/click`

- **POST** — Increment Banner Click Route

### `/api/banners/{banner_id}/order`

- **PUT** — Update Banner Order Route

### `/api/banners/{banner_id}/status`

- **PUT** — Update Banner Status Route

### `/api/banners/{banner_id}/view`

- **POST** — Increment Banner View Route

## Cart

### `/api/cart`

- **POST** — Add Cart

### `/api/cart/user/{user_id}`

- **GET** — User Cart

### `/api/cart/user/{user_id}/clear`

- **DELETE** — Cart Clear

### `/api/cart/user/{user_id}/select-all`

- **PUT** — Select All Cart

### `/api/cart/user/{user_id}/validate`

- **POST** — Cart Validate

### `/api/cart/{cart_id}`

- **GET** — Get Cart
- **DELETE** — Remove Cart

### `/api/cart/{cart_id}/move-to-cart`

- **PUT** — Cart Move To Cart

### `/api/cart/{cart_id}/quantity`

- **PUT** — Update Quantity

### `/api/cart/{cart_id}/restore`

- **PUT** — Restore Cart

### `/api/cart/{cart_id}/save-for-later`

- **PUT** — Cart Save For Later

### `/api/cart/{cart_id}/select`

- **PUT** — Select Cart

## Categories

### `/api/categories`

- **POST** — Create Category Route
- **GET** — Get Categories Route

### `/api/categories/featured`

- **GET** — Get Featured Categories Route

### `/api/categories/search`

- **GET** — Search Categories Route

### `/api/categories/slug/{slug}`

- **GET** — Get Category By Slug Route

### `/api/categories/{category_id}`

- **GET** — Get Category By Id Route
- **PUT** — Update Category Route
- **DELETE** — Delete Category Route

### `/api/categories/{category_id}/move`

- **PUT** — Move Category Route

### `/api/categories/{category_id}/product-count`

- **PUT** — Update Product Count Route

### `/api/categories/{category_id}/status`

- **PUT** — Update Category Status Route

### `/api/categories/{category_id}/subcategories`

- **GET** — Get Subcategories Route

### `/api/categories/{category_id}/view`

- **POST** — Increment Category View Route

## Coupons

### `/api/coupons`

- **POST** — Create Coupon Route
- **GET** — Get Coupons Route

### `/api/coupons/calculate-discount`

- **POST** — Calculate Coupon Discount Route

### `/api/coupons/code/{coupon_code}`

- **GET** — Get Coupon By Code Route

### `/api/coupons/refresh-status`

- **POST** — Refresh Coupon Status Route

### `/api/coupons/validate`

- **POST** — Validate Coupon Route

### `/api/coupons/{coupon_id}`

- **GET** — Get Coupon By Id Route
- **PUT** — Update Coupon Route
- **DELETE** — Delete Coupon Route

### `/api/coupons/{coupon_id}/activate`

- **POST** — Activate Coupon Route

### `/api/coupons/{coupon_id}/pause`

- **POST** — Pause Coupon Route

### `/api/coupons/{coupon_id}/status`

- **PUT** — Update Coupon Status Route

### `/api/coupons/{coupon_id}/usage`

- **POST** — Increment Coupon Usage Route

## Health

### `/api/health`

- **GET** — Health Check

## Offers

### `/api/offers`

- **POST** — Create Offer Route
- **GET** — Get Offers Route

### `/api/offers/active`

- **GET** — Get Active Offers Route

### `/api/offers/code/{offer_code}`

- **GET** — Get Offer By Code Route

### `/api/offers/refresh-status`

- **POST** — Refresh Offer Status Route

### `/api/offers/{offer_id}`

- **GET** — Get Offer Route
- **PUT** — Update Offer Route
- **DELETE** — Delete Offer Route

### `/api/offers/{offer_id}/activate`

- **POST** — Activate Offer Route

### `/api/offers/{offer_id}/calculate`

- **POST** — Calculate Offer Discount Route

### `/api/offers/{offer_id}/pause`

- **POST** — Pause Offer Route

### `/api/offers/{offer_id}/status`

- **PUT** — Update Offer Status Route

### `/api/offers/{offer_id}/usage`

- **POST** — Increment Offer Usage Route

## Orders

### `/api/orders`

- **POST** — Create New Order
- **GET** — All Orders

### `/api/orders/number/<order_number>`

- **GET** — Get Order Number

### `/api/orders/user/{user_id}`

- **GET** — User Orders

### `/api/orders/{order_id}`

- **GET** — Get Order
- **DELETE** — Delete Order Route

### `/api/orders/{order_id}/cancel`

- **PUT** — Cancel New Order

### `/api/orders/{order_id}/confirm`

- **PUT** — Confirm New Order

### `/api/orders/{order_id}/deliver`

- **PUT** — Deliver New Order

### `/api/orders/{order_id}/pack`

- **PUT** — Pack New Order

### `/api/orders/{order_id}/process`

- **PUT** — Process New Order

### `/api/orders/{order_id}/refund`

- **PUT** — Update Order Refund

### `/api/orders/{order_id}/return`

- **POST** — Return Order

### `/api/orders/{order_id}/ship`

- **PUT** — Ship New Order

### `/api/orders/{order_id}/status`

- **PUT** — Change Order Status

### `/api/orders/{order_id}/tracking`

- **PUT** — Update Order Tracking

## Payments

### `/api/payments`

- **POST** — Create Payment Route
- **GET** — Get Payments Route

### `/api/payments/<string:payment_id>`

- **GET** — Get Payment By Id Route
- **DELETE** — Delete Payment Route

### `/api/payments/<string:payment_id>/authorize`

- **POST** — Authorize Payment Route

### `/api/payments/<string:payment_id>/cancel`

- **POST** — Cancel Payment Route

### `/api/payments/<string:payment_id>/capture`

- **POST** — Capture Payment Route

### `/api/payments/<string:payment_id>/fail`

- **POST** — Fail Payment Route

### `/api/payments/<string:payment_id>/process`

- **POST** — Process Payment Route

### `/api/payments/<string:payment_id>/refund`

- **POST** — Create Refund Route

### `/api/payments/<string:payment_id>/status`

- **PUT** — Update Payment Status Route

### `/api/payments/<string:payment_id>/verify`

- **PUT** — Verify Payment Route

### `/api/payments/order/<string:order_id>`

- **GET** — Get Payment By Order Id Route

### `/api/payments/transaction/<string:transaction_id>`

- **GET** — Get Payment By Transaction Id Route

### `/api/payments/user`

- **GET** — Get User Payments Route

### `/api/payments/webhook`

- **POST** — Process Webhook Route

## Products

### `/api/products`

- **POST** — Create Product Route
- **GET** — Search Products Route

### `/api/products/<string:product_id>`

- **GET** — Get Product By Id Route
- **PUT** — Update Product Route
- **DELETE** — Delete Product Route

### `/api/products/<string:product_id>/cart-count`

- **POST** — Update Cart Count Route

### `/api/products/<string:product_id>/images`

- **POST** — Create Product Image Route
- **GET** — Get Product Images Route

### `/api/products/<string:product_id>/images/upload`

- **POST** — Upload Product Image Route

### `/api/products/<string:product_id>/purchase-count`

- **POST** — Increment Purchase Count Route

### `/api/products/<string:product_id>/status`

- **PUT** — Update Product Status Route

### `/api/products/<string:product_id>/stock-status`

- **PUT** — Update Stock Status Route

### `/api/products/<string:product_id>/view`

- **POST** — Increment Product View Route

### `/api/products/<string:product_id>/wishlist-count`

- **POST** — Update Wishlist Count Route

### `/api/products/bestsellers`

- **GET** — Get Bestseller Products Route

### `/api/products/featured`

- **GET** — Get Featured Products Route

### `/api/products/highlights/{highlight_id}`

- **GET** — Get Highlight By Id Route
- **PUT** — Update Highlight Route
- **DELETE** — Delete Highlight Route

### `/api/products/highlights/{highlight_id}/status`

- **PUT** — Update Highlight Status Route

### `/api/products/images/<string:image_id>`

- **GET** — Get Product Image Route
- **PUT** — Update Product Image Route
- **DELETE** — Delete Product Image Route

### `/api/products/images/<string:image_id>/primary`

- **PUT** — Set Primary Product Image Route

### `/api/products/images/<string:image_id>/status`

- **PUT** — Update Product Image Status Route

### `/api/products/images/<string:image_id>/thumbnail`

- **PUT** — Set Thumbnail Product Image Route

### `/api/products/new-arrivals`

- **GET** — Get New Arrivals Route

### `/api/products/ratings/{rating_id}`

- **GET** — Get Rating By Id Route
- **PUT** — Update Rating Route
- **DELETE** — Delete Rating Route

### `/api/products/ratings/{rating_id}/status`

- **PUT** — Update Rating Status Route

### `/api/products/sku/<string:sku>`

- **GET** — Get Product By Sku Route

### `/api/products/slug/<path:slug>`

- **GET** — Get Product By Slug Route

### `/api/products/specifications/{specification_id}`

- **GET** — Get Specification
- **PUT** — Update Specification
- **DELETE** — Delete Specification

### `/api/products/specifications/{specification_id}/status`

- **PUT** — Update Specification Status

### `/api/products/trending`

- **GET** — Get Trending Products Route

### `/api/products/variants/{variant_id}`

- **GET** — Get Variant
- **PUT** — Update Variant
- **DELETE** — Delete Variant

### `/api/products/variants/{variant_id}/status`

- **PUT** — Update Variant Status

### `/api/products/{product_id}/details`

- **GET** — Product Details

### `/api/products/{product_id}/highlights`

- **POST** — Create Highlight Route
- **GET** — Get Highlights Route

### `/api/products/{product_id}/rating`

- **POST** — Create Product Rating
- **GET** — Get Product Rating Route

### `/api/products/{product_id}/ratings`

- **GET** — Get Product Ratings Route

### `/api/products/{product_id}/reviews`

- **POST** — Create Product Review
- **GET** — Product Reviews

### `/api/products/{product_id}/reviews/summary`

- **GET** — Review Summary Route

### `/api/products/{product_id}/specifications`

- **POST** — Create Specification
- **GET** — Get Specifications

### `/api/products/{product_id}/variants`

- **POST** — Create Variant
- **GET** — Get Variants

## Reviews

### `/api/reviews/{review_id}`

- **GET** — Get Review
- **PUT** — Update Review Route
- **DELETE** — Delete Review Route

### `/api/reviews/{review_id}/featured`

- **PUT** — Feature Review Route

### `/api/reviews/{review_id}/helpful`

- **POST** — Review Helpful Route

### `/api/reviews/{review_id}/moderation`

- **PUT** — Moderate Review Route

### `/api/reviews/{review_id}/report`

- **POST** — Report Review Route

### `/api/reviews/{review_id}/seller-response`

- **PUT** — Seller Response Route

## Users

### `/api/users`

- **POST** — Create User Route

### `/api/users/<string:user_id>`

- **GET** — Get User By Id Route
- **PUT** — Update User Profile Route
- **DELETE** — Delete User Route

### `/api/users/<string:user_id>/change-password`

- **PUT** — Change Password Route

### `/api/users/<string:user_id>/status`

- **PUT** — Update User Status Route

### `/api/users/email/<path:email>`

- **GET** — Get User By Email Route

### `/api/users/forgot-password`

- **POST** — Forgot Password Route

### `/api/users/login`

- **POST** — Login User Route

### `/api/users/reset-password`

- **POST** — Reset Password Route

### `/api/users/verify-email`

- **POST** — Verify Email Route

### `/api/users/{user_id}/reviews`

- **GET** — User Reviews

## Wishlist

### `/api/wishlist`

- **POST** — Add Wishlist

### `/api/wishlist/check`

- **GET** — Check Wishlist

### `/api/wishlist/product/{product_id}`

- **DELETE** — Remove Wishlist Product

### `/api/wishlist/user/{user_id}`

- **GET** — User Wishlist

### `/api/wishlist/user/{user_id}/clear`

- **DELETE** — Clear User Wishlist

### `/api/wishlist/user/{user_id}/out-of-stock`

- **GET** — Out Of Stock Items

### `/api/wishlist/user/{user_id}/price-drops`

- **GET** — Price Drop Items

### `/api/wishlist/user/{user_id}/refresh-prices`

- **POST** — Refresh Prices

### `/api/wishlist/{wishlist_id}`

- **GET** — Get Wishlist
- **DELETE** — Remove Wishlist
- **PUT** — Update Wishlist

### `/api/wishlist/{wishlist_id}/restore`

- **PUT** — Restore Wishlist

---

Generated automatically from Flask registered routes.
