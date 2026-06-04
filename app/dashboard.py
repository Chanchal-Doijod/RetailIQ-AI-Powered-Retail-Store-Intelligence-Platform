from app.analytics import get_store_summary
from app.zone_analytics import get_zone_analytics
from app.top_brands import get_top_brands
from app.top_products import get_top_products
from app.dwell import get_dwell_analytics

from app.metrics import calculate_metrics
from app.funnel import calculate_funnel


def get_dashboard():

    business = get_store_summary("ST1008")

    camera = calculate_metrics("store2")

    return {

        "revenue":
        business.get("revenue", 0),

        "transactions":
        business.get("transactions", 0),

        "top_brand":
        business.get("top_brand"),

        "top_product":
        business.get("top_product"),

        "footfall":
        camera.get("total_visitors", 0),

        "staff":
        camera.get("total_staff", 0),

        "conversion_rate":
        round(
            camera.get("conversion_rate", 0) * 100,
            2
        ),

        "reentries":
        camera.get("total_reentries", 0),

        "zones":
        get_zone_analytics(),

        "top_brands":
        get_top_brands(),
        

        "top_products":
        get_top_products(),

        "funnel":
        calculate_funnel("store2"),

        "dwell":
        get_dwell_analytics()
    }