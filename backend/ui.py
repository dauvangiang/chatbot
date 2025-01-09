import grpc
channel = grpc.insecure_channel('localhost:50051')
# Đóng kết nối khi không còn sử dụng
channel.close()
