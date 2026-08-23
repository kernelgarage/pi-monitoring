#!/bin/bash
METRICS_FILE="/tmp/rpi_metrics.prom"

while true; do
  TEMP=$(vcgencmd measure_temp | egrep -o '[0-9.]+')
  
  # Hent hex (f.eks 0x0) og konverter til desimaltall (0)
  THROTTLED_HEX=$(vcgencmd get_throttled | cut -d'=' -f2)
  THROTTLED=$(printf "%d\n" "$THROTTLED_HEX" 2>/dev/null || echo 0)

  CLOCK=$(vcgencmd measure_clock arm | cut -d'=' -f2)
  VOLT=$(vcgencmd measure_volts core | cut -d'=' -f2 | sed 's/V//')

  # Viftehastighet for Pi 5
  if [ -f /sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input ]; then
    FAN_RPM=$(cat /sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input)
  elif [ -f /sys/class/hwmon/hwmon*/fan1_input ]; then
    FAN_RPM=$(cat /sys/class/hwmon/hwmon*/fan1_input | head -n 1)
  else
    FAN_RPM=0
  fi

  cat <<EOF > ${METRICS_FILE}.tmp
# HELP rpi_cpu_temperature_celsius Core temperature in Celsius
# TYPE rpi_cpu_temperature_celsius gauge
rpi_cpu_temperature_celsius $TEMP

# HELP rpi_throttled_state Throttled state bitmask
# TYPE rpi_throttled_state gauge
rpi_throttled_state $THROTTLED

# HELP rpi_cpu_clock_hz ARM CPU frequency in Hz
# TYPE rpi_cpu_clock_hz gauge
rpi_cpu_clock_hz $CLOCK

# HELP rpi_core_volts Core voltage
# TYPE rpi_core_volts gauge
rpi_core_volts $VOLT

# HELP rpi_fan_speed_rpm Cooling fan speed in RPM
# TYPE rpi_fan_speed_rpm gauge
rpi_fan_speed_rpm $FAN_RPM
EOF

  mv ${METRICS_FILE}.tmp ${METRICS_FILE}
  chmod 644 ${METRICS_FILE}
  sleep 10
done
