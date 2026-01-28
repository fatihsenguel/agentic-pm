1. Get methods in python file
>> python -c "from portfolio_tool.data_manager import DataManager; print([m for m in dir(DataManager) if not m.startswith('_')])"


2. manually list assets:
python -c "import sys; sys.path.insert(0, 'src'); from portfolio_tool.tools.data_tools import list_tracked_assets; print(list_tracked_assets.func())"