# Annotation Access Permissions

Types of permissions:

From discussions with potential users it is clear there is a need to have different levels of permissions, with the default being *private*, that is, only the creator of an annotation can see/edit/delete the annotation. Further levels can be *group* and *public*. A flexible solution for dealing with groups is the UNIX model, where users represent their own groups, but additional groups can be made to which multiple users can belong.

Types of operations permitted:

+ see:
+ edit:
+ delete:

The W3C working group for Web Annotations suggests to use the `audience` property for any *group*-related aspects and that *authorization* and *authentication* are not responsibilities of the annotation data model. 