import os
import sys
from cursor_register_manual import CursorRegistration

# 创建一个简单的模拟翻译器
class MockTranslator:
    def get(self, key, **kwargs):
        # 返回一个简单的占位符，因为我们只需测试记录功能
        return f"Translation for: {key}"

def test_registration_record():
    """测试注册记录功能"""
    print("开始测试注册记录功能...")
    
    # 创建带有模拟翻译器的CursorRegistration实例
    mock_translator = MockTranslator()
    registration = CursorRegistration(translator=mock_translator)
    
    # 测试保存注册记录
    email = "test@example.com"
    username = "Test User"
    password = "TestPassword123"
    
    # 获取email_config.txt文件路径
    config_file_path = registration._get_email_config_file()
    print(f"email_config.txt路径: {config_file_path}")
    
    # 测试保存记录
    result = registration._save_registration_record(email, username, password)
    print(f"保存结果: {'成功' if result else '失败'}")
    
    # 检查文件是否存在
    if os.path.exists(config_file_path):
        print(f"文件存在: {config_file_path}")
        # 显示文件内容
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n文件内容预览:")
                print("-" * 50)
                print(content[:500] + ("..." if len(content) > 500 else ""))
                print("-" * 50)
        except Exception as e:
            print(f"读取文件失败: {e}")
    else:
        print(f"文件不存在: {config_file_path}")

if __name__ == "__main__":
    test_registration_record()
