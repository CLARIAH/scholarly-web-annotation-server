
def bool_must(queries):
    if not isinstance(queries, list):
        raise TypeError("queries parameter must be a list of queries")
    return {"bool": {"must": queries}}

def bool_should(queries):
    if not isinstance(queries, list):
        raise TypeError("queries parameter must be a list of queries")
    return {"bool": {"should": queries}}

def permission_match(field, value):
    field = "permissions.{f}".format(f=field)
    return {"match": {field, value}}

def access_match(value):
    return {"match": {"permissions.access_status": value}}

def owner_match(value):
    return {"match": {"permissions.owner": value}}

def can_see_match(value):
    return {"match": {"permissions.can_see": value}}

def can_edit_match(value):
    return {"match": {"permissions.can_edit": value}}

def private_match(username):
    return bool_must([access_match("private"), owner_match(username)])

def shared_see_match(username):
    return bool_must([access_match("shared"), bool_should([owner_match(username), can_see_match(username)])])

def shared_edit_match(username):
    return bool_must([access_match("shared"), can_edit_match(username)])

def make_permission_see_query(params):
    if not params["username"]:
        # without username, anonymous access so must be public
        return access_match("public")
    if params["username"] and not params["access_status"]:
        # username without explicit access_status is assumed private access
        return private_match(params["username"])
    if params["access_status"] == "private":
        return private_match(params["username"])
    if params["access_status"] == "shared":
        return shared_see_match(params["username"])
    if params["access_status"] == "public":
        return access_match("public")
    if "shared" in params["access_status"] and "private" in params["access_status"]:
        return bool_should([private_match(params["username"]), shared_see_match(params["username"])])
    return None

def make_permission_edit_query(params):
    if params["access_status"] == "private":
        return private_match(params["username"])
    if params["access_status"] == "shared":
        return shared_edit_match(params["username"])
    if params["access_status"] == "public":
        return access_match("public")
    if "shared" in params["access_status"] and "private" in params["access_status"]:
        return bool_should(private_match(params["username"]), shared_edit_match(params["username"]))
    return None

