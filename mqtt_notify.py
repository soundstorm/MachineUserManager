import uuid
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import BinarySensor, BinarySensorInfo, Sensor, SensorInfo

def ValueOrListItem(arr, item, default):
	if item in arr:
		return arr[item]
	return default

class MqttNotify():

	def __init__(self, **kwargs):
		MAC = '%012x' % uuid.getnode()
		for i in range(1,6):
			MAC = '%s:%s' % (MAC[:i * 3 - 1], MAC[i * 3 - 1:])
		settings = Settings.MQTT(host=kwargs['host'], username=ValueOrListItem(kwargs,'username', None), password=ValueOrListItem(kwargs,'password', None))
		devname = ValueOrListItem(kwargs, 'name', 'MachineUserManager')
		devid = devname.replace(' ','_').replace('-','_')
		device = DeviceInfo(name=ValueOrListItem(kwargs, 'name', 'MachineUserManager'), manufacturer=ValueOrListItem(kwargs, 'manufacturer', 'sndstrm'), model=ValueOrListItem(kwargs, 'model', 'MachineUserManager'), identifiers=MAC)
		self.powerSensor = BinarySensor(Settings(mqtt=settings, entity=BinarySensorInfo(name='Power', unique_id=devid+'_power', device_class='power', device=device)))
		self.powerSensor.off()
		self.loginSensor = BinarySensor(Settings(mqtt=settings, entity=BinarySensorInfo(name='Logged In', unique_id=devid+'_loggedin', device_class='lock', device=device)))
		self.loginSensor.off()
		self.stateSensor = BinarySensor(Settings(mqtt=settings, entity=BinarySensorInfo(name='State', unique_id=devid+'_state', device_class='running', device=device)))
		self.stateSensor.off()
		self.remainingSensor = Sensor(Settings(mqtt=settings, entity=SensorInfo(name='Remaining', unique_id=devid+'_remaining', device_class='duration', unit_of_measurement='min', device=device)))
		self.remainingSensor.set_state(0)
	
	def setPower(self, state : bool):
		if state:
			self.powerSensor.on()
		else:
			self.powerSensor.off()

	def setLoggedIn(self, state : bool):
		if state:
			self.loginSensor.on()
		else:
			self.loginSensor.off()

	def setState(self, state : bool):
		if state:
			self.stateSensor.on()
		else:
			self.stateSensor.off()

	def setRemaining(self, state : int):
		self.remainingSensor.set_state(state)