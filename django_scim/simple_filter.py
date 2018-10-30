"""
Filter transformers are used to convert the SCIM query and filter syntax into
valid SQL queries.
"""

from django.contrib.auth import get_user_model


#field1=value1 OR field1=value2 to SQL

class SCIMSimpleUserFilterTransformer:
    """Transforms a PlyPlus parse tree into a tuple containing a raw SQL query
    and a dict with query parameters to go with the query."""

    @classmethod
    def search(cls, query):
        """Takes a SCIM 1.1 filter query and returns a Django `QuerySet` that
        contains zero or more user model instances.

        :param unicode query: a `unicode` query string.
        """
        print("Input Query: " + query)
        sql_query = query.replace('eq', '=')
        print("SQL Query: " + sql_query)

        final_query = 'select distinct u.* from auth_user u where {} order by u.id ASC'.format(sql_query)
        print("Final Query: " + final_query)
        return get_user_model().objects.raw(final_query, None)
