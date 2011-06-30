fin.modelmapper
===============

=fin.modelmapper= is an attempt to solve the multiple-model problem.
In mature systems, it's not uncommon to find single logical entities being represented by multiple models.  This is fine until some code needs to interact with multiple APIs (for example during a code-migration some functionality may be only exposed through an old API). Also, in the case of multiple-data-stores, it may be necessary to use alternate access methods for certain data access patterns.

modelmapper attempts to automate the optimisation of the mapping between these models.

For example:  if an entity X has two code models:  OldModel, and NewModel.  These classes may be expensive to create, and NewModel objects contain references to OldModel objects.

Now let's say you're provided an instance of NewModel for this entity, and you need code on OldModel, the fastest way to get this is to call new_model.get_old_model().  But maybe in a different circumstance, you only have X's id.  In that case, it's faster to create OldModel directly.

Working out the optimal 'route' from what you have to what you need is complex, and is easily broken by other code changes.  This module tries to make creating such mappers, and maintaining them eas(y|ier).


Furthermore, there may be cases where both models independently provide identical functionality, and therefore branching the code for each case is hard to maintin.  modelmapper can help with this situation too.

usage
------

 1. Define a mapper class that subclasses fin.modelmapper.map.Mapped
 2. for each model/property that can be derived from other models, add an appropriate name = fin.modelmapper.map.model("name") property (see fin.modelmapper.map_test.TestModel for an example)
 3. write short methods to actually perform the mappings
 4. define the maps, and what they map to what in the MODEL_MAP class attribute
 5. write a function that creates instances of this class with realistic base data, and excercises the map methods you wrote.
 6. run:  `python -m fin.modelmapper.util profile fully.qualified.module.function_name`
 7. take the output for your class, and ## TODO
