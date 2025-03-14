import copy
from cereal import car
from selfdrive.car.subaru.values import CAR

VisualAlert = car.CarControl.HUDControl.VisualAlert

def subaru_checksum(packer, values, addr):
  dat = packer.make_can_msg(addr, 0, values)[2]
  dat = [ord(i) for i in dat]
  return (sum(dat[1:]) + (addr >> 8) + addr) & 0xff

def create_steering_control(packer, car_fingerprint, apply_steer, frame, steer_step):

  if car_fingerprint == CAR.IMPREZA:
    #counts from 0 to 15 then back to 0 + 16 for enable bit
    idx = ((frame // steer_step) % 16)

    values = {
      "Counter": idx,
      "LKAS_Output": apply_steer,
      "LKAS_Request": 1 if apply_steer != 0 else 0,
      "SET_1": 1
    }
    values["Checksum"] = subaru_checksum(packer, values, 0x122)

  if car_fingerprint in (CAR.OUTBACK, CAR.LEGACY):

    if apply_steer != 0:
      chksm_steer = apply_steer * -1
      chksm_engage = 1
    else:
      chksm_steer = 0
      chksm_engage = 0

    #counts from 0 to 7 then back to 0
    idx = (frame / steer_step) % 8
    steer2 = (chksm_steer >> 8) & 0x1F
    steer1 =  chksm_steer - (steer2 << 8)
    checksum = (idx + steer2 + steer1 + chksm_engage) % 256

    values = {
      "Counter": idx,
      "LKAS_Command": apply_steer,
      "LKAS_Active": 1 if apply_steer != 0 else 0,
      "Checksum": checksum
    }

  return packer.make_can_msg("ES_LKAS", 0, values)

def create_steering_status(packer, car_fingerprint, apply_steer, frame, steer_step):

  if car_fingerprint == CAR.IMPREZA:
    values = {}
    values["Checksum"] = subaru_checksum(packer, {}, 0x322)

  return packer.make_can_msg("ES_LKAS_State", 0, values)

def create_es_distance(packer, es_distance_msg, pcm_cancel_cmd):

  values = copy.copy(es_distance_msg)
  if pcm_cancel_cmd:
    values["Main"] = 1

  values["Checksum"] = subaru_checksum(packer, values, 545)

  return packer.make_can_msg("ES_Distance", 0, values)

def create_es_lkas(packer, es_lkas_msg, visual_alert, left_line, right_line):

  values = copy.copy(es_lkas_msg)
  if visual_alert == VisualAlert.steerRequired:
    values["Keep_Hands_On_Wheel"] = 1

  values["LKAS_Left_Line_Visible"] = int(left_line)
  values["LKAS_Right_Line_Visible"] = int(right_line)

  values["Checksum"] = subaru_checksum(packer, values, 802)

  return packer.make_can_msg("ES_LKAS_State", 0, values)

def create_door_control(packer):
    values = {
      "DOOR_OPEN_FR": 1,
      "_UNKNOWN": 5,
    }
    return packer.make_can_msg("BodyInfo", 2, values)
