1. Get methods in python file
>> python -c "from portfolio_tool.data_manager import DataManager; print([m for m in dir(DataManager) if not m.startswith('_')])"      