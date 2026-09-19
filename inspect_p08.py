import sqlite3
from sovereign.core.qualification.models import CapabilityPassport, QualificationStatus
from sovereign.core.state.models import Task, TaskStatus
import inspect
from sovereign.core.qualification.models import *

print('Passport fields:', [f for f in dir(CapabilityPassport) if not f.startswith('_')])
