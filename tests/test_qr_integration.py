import pytest

from optical_transfer.protocol import parse_frame
from optical_transfer.receiver.collector import ChunkCollector
from optical_transfer.receiver.video_scanner import VideoScanner
from optical_transfer.sender.chunker import build_payloads
from optical_transfer.sender.qr_generator import make_qr_png


def test_generated_qr_decodes_with_zxing(tmp_path):
    cv2 = pytest.importorskip("cv2")
    zxingcpp = pytest.importorskip("zxingcpp")
    import numpy as np
    source = tmp_path / "small.txt"; source.write_bytes("离线传输".encode() * 50)
    _, payloads = build_payloads(source, 500)
    png = make_qr_png(payloads[0])
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    image = cv2.resize(image, (900, 900), interpolation=cv2.INTER_NEAREST)
    results = zxingcpp.read_barcodes(image)
    assert results
    assert parse_frame(results[0].text).index == 0


def test_generated_test_video_scans_and_reports_progress(tmp_path):
    cv2 = pytest.importorskip("cv2")
    pytest.importorskip("zxingcpp")
    import numpy as np
    source = tmp_path / "video-source.bin"; source.write_bytes(b"video roundtrip" * 8)
    meta, payloads = build_payloads(source, 500)
    image = cv2.imdecode(np.frombuffer(make_qr_png(payloads[0]), dtype=np.uint8), cv2.IMREAD_COLOR)
    image = cv2.resize(image, (800, 800), interpolation=cv2.INTER_NEAREST)
    path = str(tmp_path / "qr-test.avi")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (800, 800))
    if not writer.isOpened(): pytest.skip("当前 OpenCV 构建不支持 MJPG 测试编码")
    for _ in range(12): writer.write(image)
    writer.release()
    collector = ChunkCollector(); updates = []
    result = VideoScanner(collector, attempts_per_second=10).scan(path, updates.append)
    assert collector.complete and collector.metadata == meta
    assert result["added"] == 1
    assert updates and updates[-1]["ratio"] > 0
