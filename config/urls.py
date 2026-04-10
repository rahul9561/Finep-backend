
from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/wallet/", include("wallet.urls")),
    path("api/cibil/",include("cibil.urls")),
    path("api/eduloans/",include("eduloans.urls")),
    path("api/dashboard/",include("dashboard.urls")),
    path("api/verification/",include("verification.urls")),    
    
    # 🔥 Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # 🔥 Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # 🔥 Redoc (optional)
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]



urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)