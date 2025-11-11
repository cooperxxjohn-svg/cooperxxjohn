"""
Configuration Management for BOQ Estimation System
Centralized configuration for rates, standards, and system parameters
"""

from decimal import Decimal
from typing import Dict, Optional
import json
from pathlib import Path
import os


class BOQConfig:
    """
    Configuration manager for BOQ estimation system
    Handles DSR rates, system parameters, and regional settings
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_file: Path to JSON config file (optional)
        """
        self.config_file = config_file
        self.config = self._load_default_config()

        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)

    def _load_default_config(self) -> dict:
        """Load default configuration"""
        return {
            "version": "1.0.0",
            "region": "Delhi",
            "currency": "INR",
            "dsr_year": "2024",

            # Labour rates (per day in INR)
            "labour_rates": {
                "LABOUR_UNSKILLED": 600.0,
                "LABOUR_SKILLED": 800.0,
                "LABOUR_MASON": 850.0,
                "LABOUR_HELPER": 600.0,
                "LABOUR_CARPENTER": 900.0,
                "LABOUR_BARBENDER": 850.0,
                "LABOUR_PLUMBER": 850.0,
                "LABOUR_ELECTRICIAN": 900.0,
                "LABOUR_PAINTER": 750.0,
            },

            # Material rates
            "material_rates": {
                # Cement (per kg)
                "CEMENT_OPC43": 7.50,
                "CEMENT_OPC53": 8.00,
                "CEMENT_PPC": 7.00,

                # Aggregates (per cum)
                "SAND": 1200.0,
                "SAND_COARSE": 1300.0,
                "SAND_FINE": 1250.0,
                "AGGREGATE_10MM": 1350.0,
                "AGGREGATE_20MM": 1400.0,
                "AGGREGATE_40MM": 1450.0,

                # Steel (per kg)
                "STEEL_FE415": 60.0,
                "STEEL_FE500": 65.0,
                "STEEL_FE550": 70.0,
                "STEEL_STRUCTURAL": 68.0,
                "BINDING_WIRE": 80.0,

                # Bricks (per piece)
                "BRICK_FIRST_CLASS": 6.00,
                "BRICK_SECOND_CLASS": 4.50,
                "BRICK_ENGINEERING": 8.00,
                "BRICK_FLY_ASH": 5.50,

                # Wood (per cum or rmt)
                "PLYWOOD_12MM": 1800.0,  # per sqm
                "PLYWOOD_18MM": 2200.0,
                "TIMBER_TEAK": 45000.0,  # per cum
                "TIMBER_SAL": 35000.0,
                "TIMBER_BATTEN": 60.0,  # per rmt

                # Paint (per litre)
                "PAINT_EMULSION": 280.0,
                "PAINT_ENAMEL": 350.0,
                "PAINT_PRIMER": 200.0,
                "PAINT_DISTEMPER": 150.0,

                # Others
                "WATER": 0.05,  # per litre
                "ADMIXTURE": 25.0,  # per kg
            },

            # Standard percentages
            "standard_percentages": {
                "overhead_percentage": 15.0,
                "profit_percentage": 10.0,
                "gst_percentage": 18.0,
                "contingency_percentage": 5.0,
            },

            # Wastage percentages by material
            "wastage_percentages": {
                "cement": 2.0,
                "sand": 5.0,
                "aggregate": 5.0,
                "steel": 5.0,
                "brick": 8.0,
                "timber": 10.0,
                "paint": 3.0,
                "tiles": 8.0,
            },

            # CPWD validation limits
            "validation_limits": {
                "max_overhead_percentage": 20.0,
                "max_profit_percentage": 12.0,
                "max_wastage_percentage": 20.0,
                "min_quantity_thresholds": {
                    "cum": 0.01,
                    "sqm": 0.1,
                    "m": 0.1,
                    "kg": 0.5,
                },
            },

            # API settings
            "api": {
                "anthropic_model": "claude-3-5-sonnet-20241022",
                "max_tokens": 4096,
                "pdf_dpi": 300,
            },

            # Output settings
            "output": {
                "default_output_dir": "./boq_output",
                "save_intermediate_files": True,
                "export_formats": ["json", "excel"],
            },
        }

    def get_labour_rate(self, labour_type: str) -> Decimal:
        """Get labour rate by type"""
        rate = self.config["labour_rates"].get(labour_type, 0.0)
        return Decimal(str(rate))

    def get_material_rate(self, material_code: str) -> Decimal:
        """Get material rate by code"""
        rate = self.config["material_rates"].get(material_code, 0.0)
        return Decimal(str(rate))

    def get_wastage_percentage(self, material_type: str) -> Decimal:
        """Get wastage percentage for material type"""
        wastage = self.config["wastage_percentages"].get(material_type.lower(), 5.0)
        return Decimal(str(wastage))

    def get_all_rates(self) -> Dict[str, Decimal]:
        """Get all rates combined (labour + material)"""
        rates = {}
        for key, value in self.config["labour_rates"].items():
            rates[key] = Decimal(str(value))
        for key, value in self.config["material_rates"].items():
            rates[key] = Decimal(str(value))
        return rates

    def load_from_file(self, file_path: str):
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            loaded_config = json.load(f)
            # Merge with default config
            self.config.update(loaded_config)

    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default=None):
        """Get configuration value by key (supports nested keys with '.')"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value):
        """Set configuration value by key (supports nested keys with '.')"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def update_rates(self, rate_updates: Dict[str, float]):
        """
        Update multiple rates at once

        Args:
            rate_updates: Dictionary of rate code -> new value
        """
        for code, value in rate_updates.items():
            if code in self.config["labour_rates"]:
                self.config["labour_rates"][code] = value
            elif code in self.config["material_rates"]:
                self.config["material_rates"][code] = value

    def apply_regional_multiplier(self, region_multiplier: float):
        """
        Apply regional multiplier to all rates

        Args:
            region_multiplier: Multiplier (e.g., 1.2 for 20% increase)
        """
        for key in self.config["labour_rates"]:
            self.config["labour_rates"][key] *= region_multiplier

        for key in self.config["material_rates"]:
            self.config["material_rates"][key] *= region_multiplier

    def get_api_key(self) -> Optional[str]:
        """Get Anthropic API key from environment or config"""
        return os.getenv('ANTHROPIC_API_KEY') or self.config.get('api', {}).get('api_key')


# Global default configuration instance
default_config = BOQConfig()


# Helper functions
def get_rate(item_code: str, config: Optional[BOQConfig] = None) -> Decimal:
    """
    Get rate for item code

    Args:
        item_code: Labour or material code
        config: Configuration instance (uses default if None)

    Returns:
        Rate as Decimal
    """
    cfg = config or default_config
    return cfg.get_material_rate(item_code) or cfg.get_labour_rate(item_code)


def create_custom_config(
    region: str,
    dsr_year: str,
    rate_file: Optional[str] = None
) -> BOQConfig:
    """
    Create custom configuration for specific region and year

    Args:
        region: Region name (e.g., "Mumbai", "Bangalore")
        dsr_year: DSR year (e.g., "2024")
        rate_file: Optional JSON file with custom rates

    Returns:
        BOQConfig instance
    """
    config = BOQConfig(rate_file)
    config.set('region', region)
    config.set('dsr_year', dsr_year)
    return config


if __name__ == "__main__":
    # Example usage
    print("BOQ Configuration System")
    print("=" * 80)

    # Default config
    print("\n1. Default Configuration:")
    print(f"   Region: {default_config.get('region')}")
    print(f"   DSR Year: {default_config.get('dsr_year')}")
    print(f"   Cement OPC43 rate: ₹{default_config.get_material_rate('CEMENT_OPC43')}/kg")
    print(f"   Mason rate: ₹{default_config.get_labour_rate('LABOUR_MASON')}/day")

    # Save config
    print("\n2. Saving configuration...")
    default_config.save_to_file("boq_config_sample.json")
    print("   ✓ Saved to boq_config_sample.json")

    # Custom config
    print("\n3. Creating custom config for Mumbai...")
    mumbai_config = create_custom_config("Mumbai", "2024")
    mumbai_config.apply_regional_multiplier(1.15)  # 15% higher for Mumbai
    print(f"   Cement OPC43 rate: ₹{mumbai_config.get_material_rate('CEMENT_OPC43')}/kg")
    print(f"   Mason rate: ₹{mumbai_config.get_labour_rate('LABOUR_MASON')}/day")

    print("\n" + "=" * 80)
