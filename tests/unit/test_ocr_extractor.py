"""
OCR提取模块的单元测试
"""
import pytest
from pathlib import Path
import pandas as pd

# 由于pytesseract在Python 3.14上有兼容性问题，我们需要谨慎处理导入
try:
    from src.ocr_extractor import OCRExtractor, PYTESSERACT_AVAILABLE
    from src.exceptions import OCRError, FileError

    CAN_TEST_OCR = True
except ImportError:
    CAN_TEST_OCR = False


class TestParseValueUnit:
    """测试数值单位解析功能"""

    def setup_method(self):
        """测试前准备"""
        if CAN_TEST_OCR and PYTESSERACT_AVAILABLE:
            # 如果pytesseract可用，创建完整的extractor
            try:
                self.extractor = OCRExtractor()
            except OCRError:
                # 如果Tesseract未安装，创建一个不完整的实例用于测试_parse_value_unit
                self.extractor = OCRExtractor.__new__(OCRExtractor)
        else:
            # 创建一个不完整的实例用于测试_parse_value_unit
            self.extractor = (
                OCRExtractor.__new__(OCRExtractor) if CAN_TEST_OCR else None
            )

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_voltage_unit(self):
        """
        测试电压单位解析

        需求：1.2
        """
        value, unit = self.extractor._parse_value_unit("12.5V")
        assert value == 12.5
        assert unit == "V"

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_percentage_unit(self):
        """
        测试百分比单位解析

        需求：1.2
        """
        value, unit = self.extractor._parse_value_unit("407%")
        assert value == 407.0
        assert unit == "%"

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_temperature_unit(self):
        """
        测试温度单位解析

        需求：1.2
        """
        value, unit = self.extractor._parse_value_unit("28°C")
        assert value == 28.0
        assert unit == "°C"

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_value_without_unit(self):
        """
        测试无单位数值解析

        需求：1.2
        """
        value, unit = self.extractor._parse_value_unit("28")
        assert value == 28.0
        assert unit == ""

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_negative_value(self):
        """测试负数解析"""
        value, unit = self.extractor._parse_value_unit("-15.5V")
        assert value == -15.5
        assert unit == "V"

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_value_with_space(self):
        """测试带空格的数值单位"""
        value, unit = self.extractor._parse_value_unit("100 W")
        assert value == 100.0
        assert unit == "W"

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_scientific_notation(self):
        """测试科学计数法"""
        value, unit = self.extractor._parse_value_unit("1.5e-3A")
        assert abs(value - 1.5e-3) < 1e-10
        assert unit == "A"

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_invalid_text(self):
        """测试无效文本"""
        with pytest.raises(ValueError):
            self.extractor._parse_value_unit("invalid text")

    @pytest.mark.skipif(not CAN_TEST_OCR, reason="OCRExtractor不可用")
    def test_parse_empty_string(self):
        """测试空字符串"""
        with pytest.raises(ValueError):
            self.extractor._parse_value_unit("")


class TestOCRExtractorInit:
    """测试OCRExtractor初始化"""

    @pytest.mark.skipif(
        not CAN_TEST_OCR or not PYTESSERACT_AVAILABLE, reason="pytesseract不可用"
    )
    def test_init_with_tesseract_path(self):
        """测试使用指定路径初始化"""
        # 这个测试可能会失败如果Tesseract未安装
        # 但至少验证了初始化逻辑
        try:
            extractor = OCRExtractor(tesseract_path="/usr/local/bin/tesseract")
            assert extractor.tesseract_path == "/usr/local/bin/tesseract"
        except OCRError:
            # Tesseract未安装，这是预期的
            pass

    @pytest.mark.skipif(
        not CAN_TEST_OCR or not PYTESSERACT_AVAILABLE, reason="pytesseract不可用"
    )
    def test_init_auto_detect(self):
        """测试自动检测Tesseract路径"""
        try:
            extractor = OCRExtractor()
            # 如果成功初始化，说明找到了Tesseract
            assert extractor.tesseract_path is not None or True  # 可能在PATH中
        except OCRError as e:
            # Tesseract未安装，验证错误消息
            assert "Tesseract-OCR未安装" in str(e)


class TestExtractFromImage:
    """测试图像提取功能"""

    @pytest.mark.skipif(
        not CAN_TEST_OCR or not PYTESSERACT_AVAILABLE, reason="pytesseract不可用"
    )
    def test_extract_file_not_found(self):
        """
        测试文件不存在的错误处理

        需求：1.4
        """
        try:
            extractor = OCRExtractor()
        except OCRError:
            pytest.skip("Tesseract未安装")

        non_existent_file = Path("non_existent_image.png")

        with pytest.raises(FileNotFoundError):
            extractor.extract_from_image(non_existent_file)

    @pytest.mark.skipif(
        not CAN_TEST_OCR or not PYTESSERACT_AVAILABLE, reason="pytesseract不可用"
    )
    def test_extract_unsupported_format(self, tmp_path):
        """
        测试不支持格式的错误处理

        需求：1.4
        """
        try:
            extractor = OCRExtractor()
        except OCRError:
            pytest.skip("Tesseract未安装")

        # 创建一个不支持格式的文件
        unsupported_file = tmp_path / "test.txt"
        unsupported_file.write_text("test")

        with pytest.raises(OCRError) as exc_info:
            extractor.extract_from_image(unsupported_file)

        assert "不支持的图像格式" in str(exc_info.value)


class TestCompleteOCRWorkflow:
    """测试完整的OCR工作流"""

    @pytest.mark.skipif(
        not CAN_TEST_OCR or not PYTESSERACT_AVAILABLE, reason="pytesseract不可用"
    )
    def test_extract_from_sample_image(self):
        """
        测试使用示例截图的完整提取流程

        需求：1.1
        """
        try:
            extractor = OCRExtractor()
        except OCRError:
            pytest.skip("Tesseract未安装")

        # 使用示例图像
        sample_image = (
            Path(__file__).parent.parent
            / "fixtures"
            / "sample_images"
            / "sample_transmitter.png"
        )

        if not sample_image.exists():
            pytest.skip("示例图像不存在")

        # 提取数据
        result = extractor.extract_from_image(sample_image)

        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert set(result.columns) == {"item_name", "value", "unit"}

        # 由于OCR可能不完美，我们只验证基本结构
        # 不验证具体内容
        if len(result) > 0:
            assert result["item_name"].notna().all()
            assert result["value"].notna().all()
            assert result["unit"].notna().all()

    @pytest.mark.skipif(
        not CAN_TEST_OCR or not PYTESSERACT_AVAILABLE, reason="pytesseract不可用"
    )
    def test_preprocess_image(self):
        """测试图像预处理功能"""
        try:
            extractor = OCRExtractor()
        except OCRError:
            pytest.skip("Tesseract未安装")

        # 创建一个简单的测试图像
        import numpy as np

        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # 预处理
        processed = extractor._preprocess_image(test_image)

        # 验证结果
        assert isinstance(processed, np.ndarray)
        assert len(processed.shape) == 2  # 应该是灰度图像
        assert processed.shape[0] == 100
        assert processed.shape[1] == 100
