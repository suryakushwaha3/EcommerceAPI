from app import app

OUTPUT_FILE = "D:\\ShoppingAPI\\API_DOCUMENTATION.md"


def get_tag(route):
    parts = route.strip("/").split("/")

    if len(parts) < 2:
        return "Other"

    resource = parts[1]

    tag_map = {
        "users": "Users",
        "products": "Products",
        "categories": "Categories",
        "banners": "Banners",
        "cart": "Cart",
        "wishlist": "Wishlist",
        "orders": "Orders",
        "payments": "Payments",
        "reviews": "Reviews",
        "ratings": "Ratings",
        "offers": "Offers",
        "coupons": "Coupons",
    }

    return tag_map.get(
        resource,
        resource.replace("_", " ").title()
    )


def clean_methods(methods):
    return sorted(methods - {"HEAD", "OPTIONS"})


def clean_route(route):
    result = route

    for argument in [
        "user_id",
        "product_id",
        "category_id",
        "banner_id",
        "cart_id",
        "wishlist_id",
        "order_id",
        "transaction_id",
        "payment_id",
        "review_id",
        "offer_id",
        "coupon_id",
        "image_id",
        "highlight_id",
        "specification_id",
        "variant_id",
        "rating_id",
        "email",
        "sku",
        "slug",
        "offer_code",
        "coupon_code",
    ]:
        result = result.replace(
            f"<{argument}>",
            f"{{{argument}}}"
        )

    return result


def generate_documentation():

    grouped_routes = {}

    ignored_routes = {
        "/",
        "/api/docs",
        "/swagger.json",
        "/oauth2-redirect.html",
        "/apidocs/index.html",
    }

    for rule in app.url_map.iter_rules():

        route = rule.rule

        if route in ignored_routes:
            continue

        if route.startswith("/static/"):
            continue

        if route.startswith("/flasgger_static/"):
            continue

        if route.startswith("/uploads/"):
            continue

        methods = clean_methods(rule.methods)

        if not methods:
            continue

        swagger_route = clean_route(route)

        tag = get_tag(route)

        if tag not in grouped_routes:
            grouped_routes[tag] = {}

        if swagger_route not in grouped_routes[tag]:
            grouped_routes[tag][swagger_route] = []

        for method in methods:

            endpoint_name = rule.endpoint.replace(
                "_",
                " "
            ).title()

            grouped_routes[tag][swagger_route].append({
                "method": method,
                "endpoint": endpoint_name
            })

    lines = []

    lines.append("# Shopping API Documentation")
    lines.append("")

    lines.append("**Version:** 1.0.0")
    lines.append("")

    lines.append(
        "REST API for Shopping Application including "
        "Users, Products, Categories, Banners, Cart, "
        "Wishlist, Orders, Payments, Reviews, Ratings, "
        "Offers, Coupons and Product Management."
    )

    lines.append("")

    lines.append("## Base URL")
    lines.append("")

    lines.append("```text")
    lines.append("http://127.0.0.1:5000")
    lines.append("```")

    lines.append("")

    lines.append("## Swagger Documentation")
    lines.append("")

    lines.append("```text")
    lines.append("http://127.0.0.1:5000/api/docs")
    lines.append("```")

    lines.append("")

    total_endpoints = 0

    for routes in grouped_routes.values():

        for methods in routes.values():

            total_endpoints += len(methods)

    lines.append("## API Summary")
    lines.append("")

    lines.append(
        f"**Total API endpoints:** {total_endpoints}"
    )

    lines.append("")

    for tag in sorted(grouped_routes.keys()):

        lines.append(f"## {tag}")
        lines.append("")

        routes = grouped_routes[tag]

        for route in sorted(routes.keys()):

            lines.append(f"### `{route}`")
            lines.append("")

            for endpoint in routes[route]:

                method = endpoint["method"]
                name = endpoint["endpoint"]

                lines.append(
                    f"- **{method}** — {name}"
                )

            lines.append("")

    lines.append("---")
    lines.append("")

    lines.append(
        "Generated automatically from Flask "
        "registered routes."
    )

    lines.append("")

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("\n".join(lines))

    print()
    print("========================================")
    print(" API DOCUMENTATION GENERATED")
    print("========================================")
    print()

    print(f"File: {OUTPUT_FILE}")
    print(f"Total endpoints: {total_endpoints}")

    print()


if __name__ == "__main__":
    generate_documentation()