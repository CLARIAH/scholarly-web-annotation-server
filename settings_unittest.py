#adapt to your needs
server_config = {
    "Elasticsearch": {
        "host": "localhost",
        "port": 9200,
        "annotation_index": "swa_unittest",
        "user_index": "swa_user_unittest",
        "page_size": 1000
    },
    "SWAServer": {
        "host": "0.0.0.0",
        "port": "3000"
    },
    "user1": {
        "username": "user1",
        "password": "pass1"
    },
    "user2": {
        "username": "user2",
        "password": "pass2"
    }
}