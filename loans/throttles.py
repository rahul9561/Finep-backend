from rest_framework.throttling import UserRateThrottle


class LeadThrottle(UserRateThrottle):
    rate = "5/min"