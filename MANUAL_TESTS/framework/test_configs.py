"""
Test Configuration - Declarative test specifications.

Replaces scattered manual setup with structured configurations.
"""

from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from framework.phase_manager import PhaseDefinition


@dataclass
class TestConfiguration:
    """Complete test specification - replaces scattered manual setup."""
    id: int
    name: str
    description: str
    grid_size: tuple[int, int]
    agent_count: int
    resource_density: float
    perception_radius: int
    preference_mix: str  # "mixed", "cobb_douglas", "leontief", "perfect_substitutes"
    seed: int
    viewport_size: int = 600
    custom_phases: Optional[List['PhaseDefinition']] = None
    debug_categories: Optional[List[str]] = None


# All current tests defined as configurations
TEST_1_BASELINE = TestConfiguration(
    id=1,
    name="Baseline Unified Target Selection",
    description="Validates unified target selection behavior with mixed preferences",
    grid_size=(30, 30),
    agent_count=20,
    resource_density=0.25,
    perception_radius=8,
    preference_mix="mixed",
    seed=12345
)

TEST_2_SPARSE = TestConfiguration(
    id=2,
    name="Sparse Long-Range",
    description="Tests distance-based decisions with sparse resources and long perception",
    grid_size=(50, 50),
    agent_count=10,
    resource_density=0.1,
    perception_radius=15,
    preference_mix="mixed",
    seed=67890
)

TEST_3_HIGH_DENSITY = TestConfiguration(
    id=3,
    name="High Density Local",
    description="Tests crowding behavior with many agents and short perception",
    grid_size=(15, 15),
    agent_count=30,
    resource_density=0.8,
    perception_radius=3,
    preference_mix="mixed",
    seed=11111
)

TEST_4_LARGE_WORLD = TestConfiguration(
    id=4,
    name="Large World Global",
    description="Tests global perception in sparse large world",
    grid_size=(60, 60),
    agent_count=15,
    resource_density=0.05,
    perception_radius=25,  # Global awareness in large world
    preference_mix="mixed",
    seed=22222
)

TEST_5_COBB_DOUGLAS = TestConfiguration(
    id=5,
    name="Pure Cobb-Douglas",
    description="Tests balanced utility optimization with single preference type",
    grid_size=(25, 25),
    agent_count=25,
    resource_density=0.4,
    perception_radius=6,
    preference_mix="cobb_douglas",
    seed=44444
)

TEST_6_LEONTIEF = TestConfiguration(
    id=6,
    name="Pure Leontief",
    description="Tests complementary resource behavior with Leontief preferences",
    grid_size=(25, 25),
    agent_count=25,
    resource_density=0.4,
    perception_radius=6,
    preference_mix="leontief",
    seed=66666
)

TEST_7_PERFECT_SUBSTITUTES = TestConfiguration(
    id=7,
    name="Pure Perfect Substitutes",
    description="Tests interchangeable resource behavior",
    grid_size=(25, 25),
    agent_count=25,
    resource_density=0.4,
    perception_radius=6,
    preference_mix="perfect_substitutes",
    seed=88888
)

# Registry for easy access
ALL_TEST_CONFIGS = {
    1: TEST_1_BASELINE,
    2: TEST_2_SPARSE,
    3: TEST_3_HIGH_DENSITY,
    4: TEST_4_LARGE_WORLD,
    5: TEST_5_COBB_DOUGLAS,
    6: TEST_6_LEONTIEF,
    7: TEST_7_PERFECT_SUBSTITUTES
}