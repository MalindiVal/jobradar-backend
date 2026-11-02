import os
os.environ["DATABASE_URL"] = "sqlite:///./test_jobradar.db"
os.environ["SCHEDULER_ENABLED"] = "false"
os.environ["COLLECTION_SOURCES"] = ""
