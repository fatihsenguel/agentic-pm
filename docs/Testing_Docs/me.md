1.                     if os.environ.get("USE_MOCK_QUOTA") == "True":
                        quota_mgr = MockQuotaManager()
                    else:
                        quota_mgr = DatabaseQuotaManager(



2. 