# Annotation Access Permissions

## Permission Requirements

### Levels of permissions

From discussions with potential users it is clear there is a need to have different levels of permissions, with the default being *private*, that is, only the creator of an annotation can see/edit/delete the annotation. Further levels can be *group* and *public*. A flexible solution for dealing with groups is the UNIX model, where users represent their own groups, but additional groups can be made to which multiple users can belong.

### Transferring permissions

Each annotation must have see/edit/delete permissions for at least one user (typically the creator), but there may be a need to transfer permissions to another user. It may also be desirable to transfer full permissions to a group of users.

### Operations permitted

The most basic permission is being able to read/see/view an annotation. Given that a user can create, retrieve, edit, and remove annotations, it makes sense to have separate permissions for different *operations*, e.g. seeing, changing and removing (**question: should changing and removing be a single operational permission?**). This can also be based on the UNIX model for read/write/execute permissions. The *execute* operation in UNIX has no meaningful correspondence in the annotation domain, so it can be discarded.

This results in the following list of requirements:

+ R1: there should be permission levels for owner, group and public.
+ R2: operation types should have their own permissions.
+ R3: ownership should be transferrable. 
+ R4: owners should be able to change operation permissions per level and per group.

## Permission model

Types of permissions:

+ **owner**: the user who is the owner of the annotation. By default, this is the creator of the annotation, but it should be possible to transfer ownership to other users or groups of users. The owner can only be a single entity, e.g. either a single user or a single group.
+ **group**: the group(s) who have access to the annotation. Each user represents their own group. Additional groups can be made that can have multiple members. Users may want to share an annotation with multiple users and/or multi-user groups, so this can be a list of groups (single-user and multi-user groups).
+ **public**: the public represents any user. The server may return *public* annotations for requests without an authenticated user.

The owner of an annotation can have 

Types of operations permitted:

+ **read**: the permission to see/view/read an annotation. The responsibility lies with the server to return only annotations to a user who has read permissions.
+ **edit**: the permission to make changes to an annotation. Changes are timestamped via the `modified` property. To avoid overly complex permission models, there should only be a single set of properties that are allowed to be changed. The properties relation to the creation of the annotation (e.g. `creator`, `created`) should not be changeable. The server should check with each PUT request whether the user has edit permissions. The client can indicate edit permissions through e.g. an edit button. 
+ **delete**: the permission to completely remove an annotation. 

There are some issues regarding *editing* and *deleting* annotations. If an annotation is the target of a later annotation, it cannot be changed or removed without consequences. One way of dealing with this is to add a notification to annotations that target a changed/deleted annotation. Another way is to not allow changing/removing annotations that are targets of other annotations. 

### Capturing groups and permissions in annotations

The W3C working group for Web Annotations suggests to use the [audience](https://www.w3.org/TR/annotation-model/#intended-audience) property for any *group*-related aspects and that *authorization* and *authentication* are not responsibilities of the annotation data model (as discussed in this issue on GitHub: [How do we model "groups" in the Annotation Model](https://github.com/w3c/web-annotation/issues/119)). 