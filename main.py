import ggwave
import numpy as np
import sys
import os
from contextlib import contextmanager
import wave

protocols = [
    (0, "Normal"),
    (1, "Fast"),
    (2, "Fastest"),
    (3, "U-Normal"),
    (4, "U-Fast"),
    (5, "U-Fastest"),
]

snr_levels = [40, 30, 20, 15, 10, 5, 0, -5, -10, -15, -20]

def save_waveform(waveform_bytes, filename, sample_rate=48000):
    """Сохраняет float32 waveform в WAV файл"""
    audio = np.frombuffer(waveform_bytes, dtype=np.float32)
    audio_int16 = np.int16(np.clip(audio * 32767, -32768, 32767))

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

# ===== Утилиты для подавления вывода ggwave =====
@contextmanager
def suppress_output():
    """Временно подавляет stdout и stderr"""
    with open(os.devnull, 'w') as devnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = devnull, devnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


def safe_decode(instance, waveform):
    """Декодирует с подавлением вывода ggwave"""
    with suppress_output():
        return ggwave.decode(instance, waveform)


# ===== Функции работы с шумом =====
def add_noise_snr(waveform_bytes, snr_db):
    """Добавляет белый гауссовский шум с заданным SNR в дБ"""
    audio = np.frombuffer(waveform_bytes, dtype=np.float32)
    signal_power = np.sqrt(np.mean(audio ** 2))

    if signal_power < 1e-10:
        return waveform_bytes

    noise_power = signal_power / (10 ** (snr_db / 20))
    noise = np.random.normal(0, noise_power, size=audio.shape)
    noisy_audio = np.clip(audio + noise, -1.0, 1.0)

    return noisy_audio.astype(np.float32).tobytes()


def calculate_signal_power(waveform_bytes):
    """Вычисляет RMS мощность сигнала"""
    audio = np.frombuffer(waveform_bytes, dtype=np.float32)
    return np.sqrt(np.mean(audio ** 2))


# ===== Основной тест =====
def test_noise_resistance():
    message = "hello python"

    print("=" * 80)
    print("🔊 ТЕСТ УСТОЙЧИВОСТИ GGWAVE К ШУМУ")
    print("=" * 80)
    print(f"Сообщение: '{message}'")
    print(f"Формат: float32 PCM, диапазон [-1.0, 1.0]")
    print()


    # Структура для накопления результатов: {protocol_name: {snr: status}}
    all_results = {}
    protocol_info = {}

    for protocol_id, protocol_name in protocols:
        waveform = ggwave.encode(message, protocolId=protocol_id, volume=20)
        power = calculate_signal_power(waveform)
        audio = np.frombuffer(waveform, dtype=np.float32)

        protocol_info[protocol_name] = {
            'id': protocol_id,
            'power': power,
            'range': (audio.min(), audio.max()),
            'length': len(waveform),
            'samples': len(audio)
        }

        instance = ggwave.init()
        results = {}

        for snr in snr_levels:
            noisy_waveform = add_noise_snr(waveform, snr)

            text = safe_decode(instance, noisy_waveform)

            try:
                decoded = text.decode('utf-8') if text else None
                status = "✅ OK" if decoded == message else "❌ FAIL"
            except:
                status = "❌ FAIL"
            save_waveform(noisy_waveform, f'{status}_{protocol_name}-SNR[{snr}].wav')
            results[snr] = status

        # ggwave.destroy(instance)
        ggwave.free(instance)
        all_results[protocol_name] = results

        # Инфо о протоколе
        info = protocol_info[protocol_name]
        print(f"📡 {protocol_name} (ID={info['id']}): "
              f"RMS={info['power']:.4f}, "
              f"диапазон=[{info['range'][0]:.3f}, {info['range'][1]:.3f}], "
              f"{info['samples']} сэмплов")

    print()
    print("=" * 80)
    print("📊 СВОДНЫЙ ОТЧЁТ")
    print("=" * 80)

    # Заголовок таблицы
    header = f"{'SNR (дБ)':>10}"
    for proto_name in all_results.keys():
        header += f" | {proto_name:>10}"
    print(header)
    print("-" * len(header))

    # Строки результатов
    for snr in snr_levels:
        row = f"{snr:>10} "
        for proto_name in all_results.keys():
            status = all_results[proto_name].get(snr, "❌ ?")
            row += f"| {status:>10}"
        print(row)

    print()
    print("=" * 80)
    print("📈 СТАТИСТИКА")
    print("=" * 80)

    for proto_name, results in all_results.items():
        ok_count = sum(1 for s in results.values() if s == "✅ OK")
        total = len(results)
        success_rate = ok_count / total * 100

        # Найдём минимальный SNR, при котором ещё работает
        working_snrs = [snr for snr, status in results.items() if status == "✅ OK"]
        min_working_snr = min(working_snrs) if working_snrs else None

        print(f"{proto_name:10} | Успех: {ok_count}/{total} ({success_rate:5.1f}%) | "
              f"Мин. рабочий SNR: {min_working_snr if min_working_snr is not None else 'N/A'} дБ")

    print()
    print("💡 Рекомендации:")
    print("   • Для зашумлённой среды используйте протокол Robust (ID=5)")
    print("   • Увеличьте volume для повышения амплитуды сигнала")
    print("   • При SNR < 0 дБ надёжная передача маловероятна")


if __name__ == "__main__":
    test_noise_resistance()
