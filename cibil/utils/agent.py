def get_real_agent(user):

    if user.has_role("AGENT"):
        return user

    if user.parent:
        return user.parent

    return user