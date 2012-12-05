Every path should be defined as:

* short path - **entity.property**
    * **entity** - entity_id or "self". "self" will be translated to current entitys id
    * **property** - name of dataproperty in property definition or "id". "id" corresponds to entity id
* long path - **entity.relationship_definition.entity_definition.property**
    * **entity** - entity_id or "self". "self" will be translated to current entitys id
    * **relationship** - relationship name or wildcard "*" (any relationship). Relationship could be preceded by minus "-" meaning reversed relationship
    * **entity_definition** - entity definition or wildard "*" (any definition)
    * **property** - name of dataproperty in property definition or "id". "id" corresponds to entity id

Path elements define formula dependencies between formula property and other entities and properties.

Formula dependencies should confine with definition of [Directed Acyclic Graph (DAG)](http://en.wikipedia.org/wiki/Directed_acyclic_graph).

Formula dependencies are stored in dag_formula table as follows:

* **property_id**  
  Property that refers to other properties or entities.  
  Always defined;
* **related_property_id**  
  Formula property has to recalculate on change of this property.  
  In case of listproperty specific member of list is referred;
* **entity_id**  
  Existance of this entity affects value of formula property;
* **dataproperty**  
  Works with **entity_id**.  
  Recalculate formula property if entity's property has changed.  
  In case of listproperty any change on any member of list triggers recalculation;
* **relationship_definition_keyname**  
  Long paths only.  
  Set NULL in case of "*";
* **reversed_relationship_definition_keyname**  
  Same as above;
* **entity_definition_keyname**  
  Same as above.

