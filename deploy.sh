rm function.zip
cd ./venv/lib/python3.8/site-packages
zip -r9 ../../../../function.zip .
cd ../../../../
zip -g function.zip lambda_function.py
aws lambda update-function-code --function-name getRlcsStats --zip-file fileb://function.zip