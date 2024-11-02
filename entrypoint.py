from scraper.scraper import get_atp_data

def lambda_handler(event, context):
    try:
        data = get_atp_data()
        return {
            'statusCode': 200,
            'body': data
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }