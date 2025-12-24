"""
Hardware API Routes
===================

REST API endpoints for hardware control.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.hardware.manager import hardware_manager
from app.hardware.neopixel_controller import NeopixelEffect
from app.services.data_logger import data_logger
from app.models.system_log import LogLevel
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ==================== Pydantic Models ====================

class LEDControlRequest(BaseModel):
    """LED control request."""
    index: int = Field(..., ge=0, le=7, description="LED index (0-7)")
    state: bool = Field(..., description="LED state (true=on, false=off)")


class RelayControlRequest(BaseModel):
    """Relay control request."""
    index: int = Field(..., ge=0, le=3, description="Relay index (0-3)")
    state: bool = Field(..., description="Relay state (true=on, false=off)")


class MotorControlRequest(BaseModel):
    """Motor control request."""
    speed: float = Field(..., ge=0, le=100, description="Motor speed (0-100%)")


class ServoControlRequest(BaseModel):
    """Servo control request."""
    angle: float = Field(..., ge=0, le=180, description="Servo angle (0-180 degrees)")


class NeopixelColorRequest(BaseModel):
    """NeoPixel color request."""
    index: Optional[int] = Field(None, ge=0, description="LED index (None for all)")
    color: str = Field(..., description="Color name or hex code (#RRGGBB)")


class NeopixelEffectRequest(BaseModel):
    """NeoPixel effect request."""
    effect: str = Field(..., description="Effect name")
    speed: Optional[float] = Field(0.05, description="Effect speed")


class LCDWriteRequest(BaseModel):
    """LCD write request."""
    text: str = Field(..., max_length=20, description="Text to display")
    row: int = Field(0, ge=0, le=3, description="Row number")
    col: int = Field(0, ge=0, le=19, description="Column number")


class SimulationValueRequest(BaseModel):
    """Request to set simulation values."""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    distance: Optional[float] = None
    motion: Optional[bool] = None
    light: Optional[int] = None


# ==================== Status Endpoints ====================

@router.get("/status")
async def get_hardware_status() -> Dict[str, Any]:
    """Get status of all hardware controllers."""
    return hardware_manager.get_status()


@router.get("/data")
async def get_current_data() -> Dict[str, Any]:
    """Get current hardware data snapshot."""
    return hardware_manager.current_data.to_dict()


# ==================== GPIO Endpoints ====================

@router.get("/gpio")
async def get_gpio_status() -> Dict[str, Any]:
    """Get GPIO status including LEDs, buttons, and relays."""
    return {
        "leds": hardware_manager.gpio.get_led_states(),
        "buttons": hardware_manager.gpio.get_button_states(),
        "relays": hardware_manager.gpio.get_relay_states()
    }


@router.post("/gpio/led")
async def control_led(request: LEDControlRequest) -> Dict[str, Any]:
    """Control an LED."""
    success = await hardware_manager.set_led(request.index, request.state)

    if success:
        await data_logger.log_device_change(
            device_type="led",
            device_id=str(request.index),
            new_state={"on": request.state},
            changed_by="user"
        )
        await data_logger.log_system_event(
            LogLevel.INFO,
            "hardware.gpio",
            f"LED {request.index} set to {'ON' if request.state else 'OFF'}",
            user_action=True
        )

    return {
        "success": success,
        "led_index": request.index,
        "state": request.state
    }


@router.post("/gpio/led/all")
async def control_all_leds(state: bool = Query(..., description="LED state")) -> Dict[str, Any]:
    """Control all LEDs."""
    success = await hardware_manager.gpio.set_all_leds(state)
    return {
        "success": success,
        "state": state,
        "leds": hardware_manager.gpio.get_led_states()
    }


@router.post("/gpio/relay")
async def control_relay(request: RelayControlRequest) -> Dict[str, Any]:
    """Control a relay."""
    success = await hardware_manager.set_relay(request.index, request.state)

    if success:
        await data_logger.log_device_change(
            device_type="relay",
            device_id=str(request.index),
            new_state={"on": request.state},
            changed_by="user"
        )
        await data_logger.log_system_event(
            LogLevel.INFO,
            "hardware.gpio",
            f"Relay {request.index} set to {'ON' if request.state else 'OFF'}",
            user_action=True
        )

    return {
        "success": success,
        "relay_index": request.index,
        "state": request.state
    }


# ==================== PWM Endpoints ====================

@router.get("/pwm")
async def get_pwm_status() -> Dict[str, Any]:
    """Get PWM status."""
    return {
        "motor_speed": hardware_manager.pwm.get_motor_speed(),
        "servo_angle": hardware_manager.pwm.get_servo_angle(),
        "outputs": hardware_manager.pwm.get_pwm_states()
    }


@router.post("/pwm/motor")
async def control_motor(request: MotorControlRequest) -> Dict[str, Any]:
    """Control motor speed."""
    success = await hardware_manager.set_motor_speed(request.speed)

    if success:
        await data_logger.log_device_change(
            device_type="motor",
            device_id="0",
            new_state={"speed": request.speed},
            changed_by="user"
        )

    return {
        "success": success,
        "speed": request.speed
    }


@router.post("/pwm/servo")
async def control_servo(request: ServoControlRequest) -> Dict[str, Any]:
    """Control servo angle."""
    success = await hardware_manager.set_servo_angle(request.angle)

    if success:
        await data_logger.log_device_change(
            device_type="servo",
            device_id="0",
            new_state={"angle": request.angle},
            changed_by="user"
        )

    return {
        "success": success,
        "angle": request.angle
    }


# ==================== Sensor Endpoints ====================

@router.get("/sensors")
async def get_sensor_readings() -> Dict[str, Any]:
    """Get all sensor readings."""
    return await hardware_manager.sensors.read_all()


@router.get("/sensors/dht")
async def get_dht_reading() -> Dict[str, Any]:
    """Get DHT temperature and humidity."""
    data = await hardware_manager.sensors.read_dht()
    if data:
        return data
    raise HTTPException(status_code=500, detail="Failed to read DHT sensor")


@router.get("/sensors/distance")
async def get_distance() -> Dict[str, float]:
    """Get ultrasonic distance reading."""
    distance = await hardware_manager.sensors.read_ultrasonic()
    if distance is not None:
        return {"distance": distance, "unit": "cm"}
    raise HTTPException(status_code=500, detail="Failed to read distance sensor")


@router.get("/sensors/motion")
async def get_motion() -> Dict[str, bool]:
    """Get PIR motion status."""
    motion = await hardware_manager.sensors.read_pir()
    return {"motion": motion}


# ==================== I2C Endpoints ====================

@router.get("/i2c/devices")
async def get_i2c_devices() -> Dict[str, Any]:
    """Get detected I2C devices."""
    return hardware_manager.i2c.get_devices()


@router.get("/i2c/scan")
async def scan_i2c() -> List[int]:
    """Scan I2C bus for devices."""
    return await hardware_manager.i2c.scan_devices()


@router.get("/i2c/bmp280")
async def get_bmp280() -> Dict[str, Any]:
    """Get BMP280 temperature and pressure."""
    data = await hardware_manager.i2c.read_bmp280()
    if data:
        return data
    raise HTTPException(status_code=500, detail="Failed to read BMP280 sensor")


@router.get("/i2c/adc")
async def get_adc_values() -> Dict[int, float]:
    """Get all ADC channel values."""
    return await hardware_manager.i2c.read_all_adc_channels()


# ==================== SPI Endpoints ====================

@router.get("/spi/mcp3008")
async def get_mcp3008_values() -> Dict[int, float]:
    """Get all MCP3008 ADC channel values."""
    return await hardware_manager.spi.read_all_mcp3008_channels()


# ==================== Display Endpoints ====================

@router.get("/display/lcd")
async def get_lcd_info() -> Dict[str, Any]:
    """Get LCD display info and content."""
    return hardware_manager.display.get_lcd_info()


@router.post("/display/lcd/write")
async def write_lcd(request: LCDWriteRequest) -> Dict[str, Any]:
    """Write text to LCD."""
    success = await hardware_manager.display.lcd_write(
        request.text, request.row, request.col
    )
    return {
        "success": success,
        "content": hardware_manager.display.get_lcd_content()
    }


@router.post("/display/lcd/clear")
async def clear_lcd() -> Dict[str, Any]:
    """Clear LCD display."""
    success = await hardware_manager.display.lcd_clear()
    return {"success": success}


@router.get("/display/oled")
async def get_oled_info() -> Dict[str, Any]:
    """Get OLED display info."""
    return hardware_manager.display.get_oled_info()


# ==================== NeoPixel Endpoints ====================

@router.get("/neopixel")
async def get_neopixel_status() -> Dict[str, Any]:
    """Get NeoPixel status."""
    return {
        "leds": hardware_manager.neopixel.get_led_states(),
        "brightness": hardware_manager.neopixel._brightness,
        "effect_running": hardware_manager.neopixel._effect_running
    }


@router.post("/neopixel/color")
async def set_neopixel_color(request: NeopixelColorRequest) -> Dict[str, Any]:
    """Set NeoPixel color."""
    from app.hardware.neopixel_controller import COLORS, RGBColor

    # Parse color
    if request.color.lower() in COLORS:
        color = COLORS[request.color.lower()]
    elif request.color.startswith("#"):
        color = RGBColor.from_hex(request.color)
    else:
        raise HTTPException(status_code=400, detail="Invalid color")

    if request.index is not None:
        success = await hardware_manager.neopixel.set_pixel(request.index, color)
    else:
        success = await hardware_manager.neopixel.set_all(color)

    return {
        "success": success,
        "leds": hardware_manager.neopixel.get_led_states()
    }


@router.post("/neopixel/effect")
async def start_neopixel_effect(request: NeopixelEffectRequest) -> Dict[str, Any]:
    """Start a NeoPixel effect."""
    try:
        effect = NeopixelEffect(request.effect)
        success = await hardware_manager.neopixel.start_effect(effect, speed=request.speed)
        return {
            "success": success,
            "effect": request.effect
        }
    except ValueError:
        available = [e.value for e in NeopixelEffect]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid effect. Available: {available}"
        )


@router.post("/neopixel/stop")
async def stop_neopixel_effect() -> Dict[str, Any]:
    """Stop current NeoPixel effect."""
    success = await hardware_manager.neopixel.stop_effect()
    return {"success": success}


@router.post("/neopixel/clear")
async def clear_neopixel() -> Dict[str, Any]:
    """Turn off all NeoPixels."""
    await hardware_manager.neopixel.stop_effect()
    success = await hardware_manager.neopixel.clear()
    return {"success": success}


# ==================== Simulation Endpoints ====================

@router.post("/simulation/values")
async def set_simulation_values(request: SimulationValueRequest) -> Dict[str, Any]:
    """Set simulation values for testing."""
    if not hardware_manager.is_simulation:
        raise HTTPException(
            status_code=400,
            detail="Not in simulation mode"
        )

    updates = {}

    if request.temperature is not None:
        hardware_manager.sensors.set_simulated_values(temperature=request.temperature)
        updates["temperature"] = request.temperature

    if request.humidity is not None:
        hardware_manager.sensors.set_simulated_values(humidity=request.humidity)
        updates["humidity"] = request.humidity

    if request.distance is not None:
        hardware_manager.sensors.set_simulated_values(distance=request.distance)
        updates["distance"] = request.distance

    if request.motion is not None:
        hardware_manager.sensors.set_simulated_values(motion=request.motion)
        updates["motion"] = request.motion

    if request.light is not None:
        hardware_manager.sensors.set_simulated_values(light=request.light)
        updates["light"] = request.light

    return {
        "success": True,
        "updates": updates
    }


@router.post("/simulation/button/{index}")
async def simulate_button_press(index: int) -> Dict[str, Any]:
    """Simulate a button press."""
    if not hardware_manager.is_simulation:
        raise HTTPException(status_code=400, detail="Not in simulation mode")

    await hardware_manager.gpio.simulate_button_press(index)
    return {"success": True, "button_index": index}
