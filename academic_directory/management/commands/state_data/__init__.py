# academic_directory/management/commands/state_data/__init__.py
"""
Aggregates all state university data into a single UNIVERSITIES list.

To add more schools:
  1. Open the relevant state file (e.g., state_data/lagos.py)
  2. Append a new university dict to that state's UNIVERSITIES list
  3. No changes needed here — everything is imported automatically.
"""

from .abia import UNIVERSITIES as _ABIA
from .adamawa import UNIVERSITIES as _ADAMAWA
from .akwa_ibom import UNIVERSITIES as _AKWA_IBOM
from .anambra import UNIVERSITIES as _ANAMBRA
from .bauchi import UNIVERSITIES as _BAUCHI
from .bayelsa import UNIVERSITIES as _BAYELSA
from .benue import UNIVERSITIES as _BENUE
from .borno import UNIVERSITIES as _BORNO
from .cross_river import UNIVERSITIES as _CROSS_RIVER
from .delta import UNIVERSITIES as _DELTA
from .ebonyi import UNIVERSITIES as _EBONYI
from .edo import UNIVERSITIES as _EDO
from .ekiti import UNIVERSITIES as _EKITI
from .enugu import UNIVERSITIES as _ENUGU
from .fct import UNIVERSITIES as _FCT
from .gombe import UNIVERSITIES as _GOMBE
from .imo import UNIVERSITIES as _IMO
from .jigawa import UNIVERSITIES as _JIGAWA
from .kaduna import UNIVERSITIES as _KADUNA
from .kano import UNIVERSITIES as _KANO
from .katsina import UNIVERSITIES as _KATSINA
from .kebbi import UNIVERSITIES as _KEBBI
from .kogi import UNIVERSITIES as _KOGI
from .kwara import UNIVERSITIES as _KWARA
from .lagos import UNIVERSITIES as _LAGOS
from .nasarawa import UNIVERSITIES as _NASARAWA
from .niger import UNIVERSITIES as _NIGER
from .ogun import UNIVERSITIES as _OGUN
from .ondo import UNIVERSITIES as _ONDO
from .osun import UNIVERSITIES as _OSUN
from .oyo import UNIVERSITIES as _OYO
from .plateau import UNIVERSITIES as _PLATEAU
from .rivers import UNIVERSITIES as _RIVERS
from .sokoto import UNIVERSITIES as _SOKOTO
from .taraba import UNIVERSITIES as _TARABA
from .yobe import UNIVERSITIES as _YOBE
from .zamfara import UNIVERSITIES as _ZAMFARA

UNIVERSITIES = (
    _ABIA
    + _ADAMAWA
    + _AKWA_IBOM
    + _ANAMBRA
    + _BAUCHI
    + _BAYELSA
    + _BENUE
    + _BORNO
    + _CROSS_RIVER
    + _DELTA
    + _EBONYI
    + _EDO
    + _EKITI
    + _ENUGU
    + _FCT
    + _GOMBE
    + _IMO
    + _JIGAWA
    + _KADUNA
    + _KANO
    + _KATSINA
    + _KEBBI
    + _KOGI
    + _KWARA
    + _LAGOS
    + _NASARAWA
    + _NIGER
    + _OGUN
    + _ONDO
    + _OSUN
    + _OYO
    + _PLATEAU
    + _RIVERS
    + _SOKOTO
    + _TARABA
    + _YOBE
    + _ZAMFARA
)
