"""
Material Database Unit Tests

Tests for material database operations, pricing lookups,
supplier integration, and material recommendations.
"""

import pytest
import json
from pathlib import Path

from materials import MaterialDatabase, SupplierAPI


# ============================================================================
# Material Database Initialization Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestMaterialDatabaseInitialization:
    """Test material database initialization"""

    def test_create_material_database_creates_file(self, tmp_path):
        """Test that creating database creates JSON file"""
        materials_file = tmp_path / "materials.json"
        db = MaterialDatabase(str(materials_file))

        assert materials_file.exists()
        assert materials_file.is_file()

    def test_material_database_initializes_with_default_data(self, tmp_path):
        """Test that new database has default materials"""
        materials_file = tmp_path / "materials.json"
        db = MaterialDatabase(str(materials_file))

        assert "paint" in db.materials
        assert "supplies" in db.materials
        assert "primer" in db.materials["paint"]
        assert "interior_paint" in db.materials["paint"]

    def test_material_database_loads_existing_file(self, tmp_path):
        """Test loading existing materials file"""
        materials_file = tmp_path / "materials.json"

        # Create database with initial data
        db1 = MaterialDatabase(str(materials_file))
        initial_count = len(db1.materials["supplies"])

        # Load same database
        db2 = MaterialDatabase(str(materials_file))

        assert len(db2.materials["supplies"]) == initial_count

    def test_material_database_has_primer_materials(self, temp_materials_db):
        """Test that database includes primer materials"""
        primers = temp_materials_db.materials["paint"]["primer"]

        assert len(primers) > 0
        assert any("Sherwin-Williams" in p["manufacturer"] for p in primers)
        assert any("Benjamin Moore" in p["manufacturer"] for p in primers)

    def test_material_database_has_interior_paint_materials(self, temp_materials_db):
        """Test that database includes interior paint"""
        paints = temp_materials_db.materials["paint"]["interior_paint"]

        assert len(paints) > 0
        assert all("coverage" in p for p in paints)
        assert all("price" in p for p in paints)

    def test_material_database_has_supplies(self, temp_materials_db):
        """Test that database includes painting supplies"""
        supplies = temp_materials_db.materials["supplies"]

        assert len(supplies) > 0
        # Check for common supplies
        supply_names = [s["name"] for s in supplies]
        assert any("Roller" in name for name in supply_names)
        assert any("Brush" in name for name in supply_names)
        assert any("Tape" in name for name in supply_names)


# ============================================================================
# Material Search Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestMaterialSearch:
    """Test material search functionality"""

    def test_search_materials_by_name(self, temp_materials_db):
        """Test searching for materials by name"""
        results = temp_materials_db.search_materials("ProMar")

        assert len(results) > 0
        assert all("ProMar" in r["name"] for r in results)

    def test_search_materials_case_insensitive(self, temp_materials_db):
        """Test that search is case-insensitive"""
        results_lower = temp_materials_db.search_materials("promar")
        results_upper = temp_materials_db.search_materials("PROMAR")

        assert len(results_lower) == len(results_upper)

    def test_search_materials_by_manufacturer(self, temp_materials_db):
        """Test searching by manufacturer name"""
        results = temp_materials_db.search_materials("Sherwin-Williams")

        assert len(results) > 0
        assert all("Sherwin-Williams" in r.get("manufacturer", "") for r in results)

    def test_search_materials_with_no_results(self, temp_materials_db):
        """Test search with no matching results"""
        results = temp_materials_db.search_materials("NonexistentProduct")

        assert len(results) == 0
        assert isinstance(results, list)

    def test_search_materials_with_category_filter(self, temp_materials_db):
        """Test searching with category filter"""
        results = temp_materials_db.search_materials("Sherwin", category="primer")

        assert len(results) > 0
        assert all(r["category"] == "primer" for r in results)

    def test_search_materials_returns_complete_data(self, temp_materials_db):
        """Test that search results include all material data"""
        results = temp_materials_db.search_materials("ProMar")

        for material in results:
            assert "id" in material
            assert "name" in material
            assert "category" in material
            assert "price" in material
            assert "unit" in material

    def test_search_supplies_category(self, temp_materials_db):
        """Test searching supplies"""
        results = temp_materials_db.search_materials("Roller")

        assert len(results) > 0
        assert any("category" in r and "roller" in r["category"].lower() for r in results)


# ============================================================================
# Material Lookup Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestMaterialLookup:
    """Test material lookup by ID"""

    def test_get_material_by_id_returns_material(self, temp_materials_db):
        """Test getting material by ID"""
        material = temp_materials_db.get_material_by_id("sw_prep_primer")

        assert material is not None
        assert material["id"] == "sw_prep_primer"
        assert material["name"] == "Sherwin-Williams PrepRite ProBlock Interior Primer"

    def test_get_material_by_id_with_invalid_id(self, temp_materials_db):
        """Test getting material with non-existent ID"""
        material = temp_materials_db.get_material_by_id("nonexistent_id")

        assert material is None

    def test_get_material_by_id_includes_all_fields(self, temp_materials_db):
        """Test that material lookup returns all fields"""
        material = temp_materials_db.get_material_by_id("sw_promar_200")

        assert "id" in material
        assert "name" in material
        assert "manufacturer" in material
        assert "category" in material
        assert "coverage" in material
        assert "price" in material
        assert "unit" in material
        assert "product_code" in material

    def test_get_supply_material_by_id(self, temp_materials_db):
        """Test getting supply item by ID"""
        material = temp_materials_db.get_material_by_id("roller_cover_9in")

        assert material is not None
        assert material["category"] == "roller"
        assert material["price"] > 0


# ============================================================================
# Recommended Materials Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestRecommendedMaterials:
    """Test material recommendations"""

    def test_get_recommended_materials_for_commercial(self, temp_materials_db):
        """Test recommended materials for commercial project"""
        recommended = temp_materials_db.get_recommended_materials("commercial")

        assert "primer" in recommended
        assert "paint" in recommended
        assert "quality" in recommended
        assert recommended["quality"] == "mid-range"

        # Should recommend Sherwin-Williams ProMar for commercial
        assert "ProMar" in recommended["paint"]["name"] or "Sherwin-Williams" in recommended["paint"]["manufacturer"]

    def test_get_recommended_materials_for_premium(self, temp_materials_db):
        """Test recommended materials for premium project"""
        recommended = temp_materials_db.get_recommended_materials("premium")

        assert recommended["quality"] == "premium"
        # Should recommend Benjamin Moore for premium
        assert "Benjamin Moore" in recommended["paint"]["manufacturer"] or "Regal" in recommended["paint"]["name"]

    def test_get_recommended_materials_for_economy(self, temp_materials_db):
        """Test recommended materials for economy project"""
        recommended = temp_materials_db.get_recommended_materials("economy")

        assert recommended["quality"] == "economy"
        # Should recommend BEHR for economy
        assert "BEHR" in recommended["paint"]["manufacturer"] or recommended["paint"]["price"] < 50

    def test_recommended_materials_include_complete_data(self, temp_materials_db):
        """Test that recommendations include complete material data"""
        recommended = temp_materials_db.get_recommended_materials("commercial")

        primer = recommended["primer"]
        assert "id" in primer
        assert "price" in primer
        assert "coverage" in primer

        paint = recommended["paint"]
        assert "id" in paint
        assert "price" in paint
        assert "coverage" in paint


# ============================================================================
# Supplies Calculation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestSuppliesCalculation:
    """Test supplies calculation for projects"""

    def test_calculate_supplies_for_small_project(self, temp_materials_db):
        """Test supplies calculation for small project"""
        supplies = temp_materials_db.calculate_supplies_needed(500.0)

        assert len(supplies) > 0
        assert all("name" in s for s in supplies)
        assert all("quantity" in s for s in supplies)
        assert all("total_price" in s for s in supplies)

    def test_calculate_supplies_includes_roller_covers(self, temp_materials_db):
        """Test that supplies include roller covers"""
        supplies = temp_materials_db.calculate_supplies_needed(2000.0)

        roller_covers = [s for s in supplies if "Roller Cover" in s["name"]]
        assert len(roller_covers) > 0
        # 1 cover per 1000 sqft
        assert roller_covers[0]["quantity"] >= 2

    def test_calculate_supplies_includes_brushes(self, temp_materials_db):
        """Test that supplies include brushes"""
        supplies = temp_materials_db.calculate_supplies_needed(1000.0)

        brushes = [s for s in supplies if "Brush" in s["name"]]
        assert len(brushes) > 0

    def test_calculate_supplies_includes_tape(self, temp_materials_db):
        """Test that supplies include painter's tape"""
        supplies = temp_materials_db.calculate_supplies_needed(1000.0)

        tape = [s for s in supplies if "Tape" in s["name"]]
        assert len(tape) > 0

    def test_calculate_supplies_includes_drop_cloths(self, temp_materials_db):
        """Test that supplies include drop cloths"""
        supplies = temp_materials_db.calculate_supplies_needed(1000.0)

        drop_cloths = [s for s in supplies if "Drop Cloth" in s["name"]]
        assert len(drop_cloths) > 0

    def test_calculate_supplies_scales_with_area(self, temp_materials_db):
        """Test that supplies scale appropriately with project area"""
        supplies_small = temp_materials_db.calculate_supplies_needed(500.0)
        supplies_large = temp_materials_db.calculate_supplies_needed(5000.0)

        # Get roller cover quantities
        rollers_small = [s for s in supplies_small if "Roller Cover" in s["name"]][0]["quantity"]
        rollers_large = [s for s in supplies_large if "Roller Cover" in s["name"]][0]["quantity"]

        assert rollers_large > rollers_small

    def test_calculate_supplies_minimum_quantities(self, temp_materials_db):
        """Test that minimum quantities are respected"""
        supplies = temp_materials_db.calculate_supplies_needed(10.0)  # Tiny area

        # Should still get minimum quantities
        for supply in supplies:
            assert supply["quantity"] >= 1

    def test_calculate_supplies_total_prices_accurate(self, temp_materials_db):
        """Test that total prices are calculated correctly"""
        supplies = temp_materials_db.calculate_supplies_needed(1000.0)

        for supply in supplies:
            expected_total = supply["quantity"] * supply["price"]
            assert abs(supply["total_price"] - expected_total) < 0.01

    def test_calculate_supplies_for_large_commercial_project(self, temp_materials_db):
        """Test supplies for large commercial project"""
        supplies = temp_materials_db.calculate_supplies_needed(50000.0)

        # Should scale up significantly
        roller_covers = [s for s in supplies if "Roller Cover" in s["name"]][0]
        assert roller_covers["quantity"] >= 50

    def test_calculate_supplies_includes_caulk(self, temp_materials_db):
        """Test that supplies include caulk"""
        supplies = temp_materials_db.calculate_supplies_needed(1000.0)

        caulk = [s for s in supplies if "Caulk" in s["name"]]
        assert len(caulk) > 0

    def test_calculate_supplies_includes_sandpaper(self, temp_materials_db):
        """Test that supplies include sandpaper"""
        supplies = temp_materials_db.calculate_supplies_needed(1000.0)

        sandpaper = [s for s in supplies if "Sandpaper" in s["name"]]
        assert len(sandpaper) > 0


# ============================================================================
# Supplier API Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestSupplierAPI:
    """Test supplier API integration (mocked)"""

    def test_supplier_api_initialization(self):
        """Test SupplierAPI initialization"""
        api = SupplierAPI()

        assert api is not None
        assert hasattr(api, 'cache')
        assert hasattr(api, 'cache_duration')

    def test_get_sherwin_williams_price_with_no_api_key(self):
        """Test SW price lookup without API key (returns None)"""
        api = SupplierAPI()
        result = api.get_sherwin_williams_price("B28W00750", "12345")

        # Without real API key, should return None
        assert result is None

    def test_get_benjamin_moore_price_with_no_api_key(self):
        """Test BM price lookup without API key (returns None)"""
        api = SupplierAPI()
        result = api.get_benjamin_moore_price("N023", "12345")

        # Without real API key, should return None
        assert result is None

    def test_get_best_price_returns_material(self):
        """Test getting best price for a material"""
        api = SupplierAPI()
        result = api.get_best_price("ProMar", "12345")

        # Should return material from database even without API
        assert result is not None
        assert "material" in result
        assert "price" in result

    def test_supplier_api_cache_structure(self):
        """Test that cache is properly structured"""
        api = SupplierAPI()

        assert isinstance(api.cache, dict)
        assert api.cache_duration.total_seconds() > 0


# ============================================================================
# Material Data Validation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestMaterialDataValidation:
    """Test that material data is valid"""

    def test_all_primers_have_required_fields(self, temp_materials_db):
        """Test that all primer materials have required fields"""
        primers = temp_materials_db.materials["paint"]["primer"]

        for primer in primers:
            assert "id" in primer
            assert "name" in primer
            assert "manufacturer" in primer
            assert "category" in primer
            assert primer["category"] == "primer"
            assert "coverage" in primer
            assert primer["coverage"] > 0
            assert "price" in primer
            assert primer["price"] > 0
            assert "unit" in primer

    def test_all_paints_have_required_fields(self, temp_materials_db):
        """Test that all paint materials have required fields"""
        paints = temp_materials_db.materials["paint"]["interior_paint"]

        for paint in paints:
            assert "id" in paint
            assert "name" in paint
            assert "manufacturer" in paint
            assert "category" in paint
            assert "coverage" in paint
            assert "price" in paint

    def test_all_supplies_have_required_fields(self, temp_materials_db):
        """Test that all supplies have required fields"""
        supplies = temp_materials_db.materials["supplies"]

        for supply in supplies:
            assert "id" in supply
            assert "name" in supply
            assert "category" in supply
            assert "price" in supply
            assert "unit" in supply

    def test_material_prices_are_reasonable(self, temp_materials_db):
        """Test that material prices are in reasonable ranges"""
        paints = temp_materials_db.materials["paint"]["interior_paint"]

        for paint in paints:
            # Paint should be between $20 and $100 per gallon
            assert 20 <= paint["price"] <= 100

    def test_material_coverage_rates_are_reasonable(self, temp_materials_db):
        """Test that coverage rates are reasonable"""
        paints = temp_materials_db.materials["paint"]["interior_paint"]

        for paint in paints:
            # Coverage should be between 200-500 sqft/gallon
            assert 200 <= paint["coverage"] <= 500


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestMaterialEdgeCases:
    """Test edge cases in material operations"""

    def test_search_materials_with_empty_query(self, temp_materials_db):
        """Test search with empty query string"""
        results = temp_materials_db.search_materials("")

        # Empty query should return nothing or everything depending on implementation
        assert isinstance(results, list)

    def test_calculate_supplies_with_zero_area(self, temp_materials_db):
        """Test supplies calculation with zero area"""
        supplies = temp_materials_db.calculate_supplies_needed(0.0)

        # Should still return minimum supplies
        assert len(supplies) > 0
        for supply in supplies:
            assert supply["quantity"] >= 1

    def test_calculate_supplies_with_negative_area(self, temp_materials_db):
        """Test supplies calculation with negative area (should handle gracefully)"""
        supplies = temp_materials_db.calculate_supplies_needed(-100.0)

        # Should handle gracefully, possibly treating as 0 or absolute value
        assert isinstance(supplies, list)

    def test_get_recommended_materials_with_unknown_type(self, temp_materials_db):
        """Test recommendations with unknown project type"""
        recommended = temp_materials_db.get_recommended_materials("unknown_type")

        # Should default to some recommendation
        assert "primer" in recommended
        assert "paint" in recommended

    def test_material_database_with_missing_file_creates_new(self, tmp_path):
        """Test that missing file is created automatically"""
        nonexistent_file = tmp_path / "nonexistent" / "materials.json"

        db = MaterialDatabase(str(nonexistent_file))

        assert nonexistent_file.exists()
        assert db.materials is not None
