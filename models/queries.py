
def bool_must(queries):
    if not isinstance(queries, list):
        raise TypeError("queries parameter must be a list of queries")
    return {"bool": {"must": queries}}

def bool_should(queries):
    if not isinstance(queries, list):
        raise TypeError("queries parameter must be a list of queries")
    return {"bool": {"should": queries}}

def make_param_filter_queries(params):
    filter_queries = []
    if "filter" not in params:
        return filter_queries
    if "target_id" in params["filter"]:
        filter_queries += [make_target_list_query({"id": params["filter"]["target_id"]})]
    elif "target_type" in params["filter"]:
        filter_queries += [make_target_list_query({"type": params["filter"]["target_type"]})]
    return filter_queries

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
    access_matches = []
    if "private" in params["access_status"]:
        access_matches += [private_match(params["username"])]
    if "shared" in params["access_status"]:
        access_matches += [shared_see_match(params["username"])]
    if "public" in params["access_status"]:
        access_matches += [access_match("public")]
    if len(access_matches) == 1:
        return bool_must(access_matches) # avoid should being interpreted as boost
    else:
        return bool_should(access_matches)

def make_permission_edit_query(params):
    access_matches = []
    if "private" in params["access_status"]:
        access_matches += [private_match(params["username"])]
    if "shared" in params["access_status"]:
        access_matches += [shared_edit_match(params["username"])]
    if "public" in params["access_status"]:
        access_matches += [access_match("public")]
    if len(access_matches) == 1:
        return bool_must(access_matches) # avoid should being interpreted as boost
    else:
        return bool_should(access_matches)

def make_target_list_query(target):
    target_field = list(target.keys())[0]
    list_field = "target_list.%s.keyword" % target_field
    if type(target[target_field]) == str:
        return {"match": {list_field: target[target_field]}}
    elif type(target[target_field]) == list:
        return bool_should([{"match": {list_field: target_item}} for target_item in target[target_field]])

