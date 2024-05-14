const getConnectorPowerKw = (voltage, ampere, num_phases) => {
  let power = 0;
  if(num_phases === 'AC_3_PHASE') {
    power = Math.sqrt(3) * voltage * ampere / 1000;
  } else {
    power = voltage * ampere / 1000;
  }
  power =  Math.round((power + Number.EPSILON) * 100) / 100
  return power
}

export default getConnectorPowerKw
