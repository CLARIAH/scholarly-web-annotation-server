from models.error import PermissionError, InvalidUsage

def is_allowed_action(username, action, annotation):
    if action == "traverse": # traversing chained annotations requires no permissions
        return True
    if action == "see":
        return is_allowed_to_see(username, annotation)
    if action == "edit":
        return is_allowed_to_edit(username, annotation)

def is_allowed_to_see(username, annotation):
    if not username:
        return is_public(annotation)
    if is_public(annotation):
        return True
    if is_owned_by(annotation, username):
        return True
    if is_see_shared_with(annotation, username):
        return True
    return False

def is_allowed_to_edit(username, annotation):
    if not username: # anonymous users are not allowed to edit
        return False
    if is_public(annotation) and not is_owned_by(annotation, username): # only owner can edit public annotation
        return False
    if is_owned_by(annotation, username):
        return True
    if is_edit_shared_with(annotation, username):
        return True
    return False

def is_owned_by(annotation, username):
    return annotation.permissions["owner"] == username

def is_see_shared_with(annotation, username):
    if not is_shared(annotation):
        return False
    if "can_see" not in annotation.permissions:
        return False
    return username in annotation.permissions["can_see"]

def is_edit_shared_with(annotation, username):
    if not is_shared(annotation):
        return False
    if "can_edit" not in annotation.permissions:
        return False
    return username in annotation.permissions["can_edit"]

def is_private(annotation):
    return "private" in annotation.permissions["access_status"]

def is_shared(annotation):
    return "shared" in annotation.permissions["access_status"]

def is_public(annotation):
    return "public" in annotation.permissions["access_status"]


def add_permissions(annotation, params):
    if not annotation.permissions: # must be new annotation
        add_permissions_to_new_annotation(annotation, params)
    elif not params: # no permissions to update
        return annotation
    else:
        update_permissions_of_existing_annotation(annotation, params)
    add_share_permissions(annotation, params)
    return annotation

def update_permissions_of_existing_annotation(annotation, params):
    if "action" in params and params["action"] == "traverse":
        return annotation
    # update of existing annotation
    if params["access_status"] != None:
        # set new access status
        annotation.permissions["access_status"] = params["access_status"]

def add_permissions_to_new_annotation(annotation, params):
    if not params:
        # no permissions passed, required for new annotation
        raise InvalidUsage("New annotations need permission parameters")
    if "username" not in params or not params["username"]:
        # new annotation must be submitted by a known user
        raise PermissionError("Cannot add annotation as unknown user")
    if not params["access_status"]:
        # new annotation, no explicit acces_status, use private as default
        params["access_status"] = ["private"]
    # new annotation, set access_status
    annotation.permissions = {
        "access_status": params["access_status"],
        "owner": params["username"]
    }

def add_share_permissions(annotation, params):
    # private and public annotations have a no share details
    if not is_shared(annotation):
        return True
    # only set can_see and can_edit permissions when they are passed as params
    if "can_see" in params:
        if not isinstance(params["can_see"], list):
            raise PermissionError("can_see parameter must have a list as value")
        annotation.permissions["can_see"] = params["can_see"]
    if "can_edit" in params:
        if not isinstance(params["can_edit"], list):
            raise PermissionError("can_edit parameter must have a list as value")
        annotation.permissions["can_edit"] = params["can_edit"]
        # make sure users who can edit are also in can_see list
        for user in params["can_edit"]:
            if user not in annotation.permissions["can_see"]:
                annotation.permissions["can_see"] += [user]

def remove_permissions(annotation):
    if "permissions" in annotation:
        del annotation.permissions

