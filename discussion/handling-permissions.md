# Annotation Access Permissions

## Permission Requirements

### Levels of permissions

From discussions with potential users it is clear there is a need to have different levels of permissions, with the default being *private*, that is, only the creator of an annotation can see/edit/delete the annotation. Further levels can be *group* and *public*. A flexible solution for dealing with groups is the UNIX model, where users represent their own groups, but additional groups can be made to which multiple users can belong.

### Transferring permissions

Each annotation must have see/edit/delete permissions for at least one user (typically the creator), but there may be a need to transfer permissions to another user. It may also be desirable to transfer full permissions to a group of users.

### Operations permitted

The most basic permission is being able to read/see/view an annotation. Given that a user can create, retrieve, edit, and remove annotations, it makes sense to have separate permissions for different *operations*, e.g. seeing, changing and removing (**question: should changing and removing be a single operational permission?**). This can also be based on the UNIX model for read/write/execute permissions. The *execute* operation in UNIX has no meaningful correspondence in the annotation domain, so it can be discarded.

### Permission model

Types of permissions:

+ user
+ group
+ public

Types of operations permitted:

+ read:
+ edit:
+ delete:

### Capturing groups and permissions in annotations

The W3C working group for Web Annotations suggests to use the [audience](https://www.w3.org/TR/annotation-model/#intended-audience) property for any *group*-related aspects and that *authorization* and *authentication* are not responsibilities of the annotation data model (as discussed in this issue on GitHub: [How do we model "groups" in the Annotation Model](https://github.com/w3c/web-annotation/issues/119)). 