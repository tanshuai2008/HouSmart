from sqlalchemy import text

class PropertyRepository:

    @staticmethod
    def create_property(db, data):

        insert_query = text("""
            INSERT INTO properties (
                formatted_address, street, city, state, zip_code,
                county_fips, tract_geoid, latitude, longitude, location
            )
            VALUES (
                :formatted_address, :street, :city, :state, :zip_code,
                :county_fips, :tract_geoid, :latitude, :longitude,
                ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
            )
            RETURNING *
        """)

        result = db.execute(insert_query, data)
        property_row = result.mappings().fetchone()
        db.commit()

        return dict(property_row)