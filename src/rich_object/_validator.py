class ObjectValidator:
    """Schema validation capabilities for Object."""

    def validate(self, schema: dict):
        """Validates the current Object against a JSON Schema.

        Args:
            schema (dict): The JSON Schema definition to validate against.

        Raises:
            ImportError: If the 'jsonschema' package is not installed.
            jsonschema.exceptions.ValidationError: If the Object does not conform to the schema.
            jsonschema.exceptions.SchemaError: If the provided schema itself is invalid.

        Returns:
            bool: True if validation succeeds. (If it fails, it raises an exception).

        Example:
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "age": {"type": "integer", "minimum": 18}
            ...     },
            ...     "required": ["age"]
            ... }
            >>> obj = Object({"age": 25})
            >>> obj.validate(schema)
            True
        """
        try:
            import jsonschema
        except ImportError:
            raise ImportError(
                "jsonschema is required to use the validate() method. "
                "Install it with 'pip install jsonschema'"
            )

        # We validate the standard Python dict representation of the Object
        jsonschema.validate(instance=self.to_dict(), schema=schema)
        
        return True
