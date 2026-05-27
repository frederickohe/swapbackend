"""Auto-generated module that imports all SQLAlchemy model modules.

Importing these modules ensures their model classes are defined and
registered on `Base.metadata` so Alembic autogenerate can detect tables.

If any import fails, the exception is printed and import proceeds.
"""
from importlib import import_module
from utilities.dbconfig import Base

# List of model modules to import (module path relative to `src`)
_model_modules = [
	"core.user.model.User",
	"core.cloudstorage.model.filemodel",
	"core.otp.model.otp",
	"core.notification.model.Notification",
	"core.histories.model.history",
	"core.auth.model.refreshtoken",
	"core.auth.model.password_reset_token",
	"core.listing.model.listing",
	"core.hub.model.hub",
	"core.swap.model.swap_request",
	"core.swap.model.swap",
	"core.payment.model.transaction",
	"core.paystack.model.paystack_session",
	"core.credit.model.credit_transaction",
]


for _m in _model_modules:
	try:
		import_module(_m)
	except Exception as _err:
		# Avoid crashing on import errors during alembic autogenerate; print for visibility
		print(f"dbmodels: failed to import {_m}: {_err}")
