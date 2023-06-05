from __future__ import annotations

# class PlayerInput:
#     def __init__(self):
#         self.action: Optional[Action] = None
#
#     @property
#     def current_member(self) -> CombatantMixIn:
#         return Arena.Instance.current
#
#     def get_action_input(self, index: int) -> Action:
#         self.action = self.current_member.get_actions()[index]
#         return self.action
#
#     def get_target_input(self, position: int) -> Targeting:
#         return self.action.targeting.choose(position)
#
#     def get_input(self) -> Optional[Decision]:
#         while True:
#             try:
#                 print(f"{self.current_member.name}'s turn")
#                 print(f"{self.current_member.get_actions()}")
#                 index = int(input("choose action: "))
#                 action = self.get_action_input(index)
#                 if action.targeting is None or not action.targeting.selective:
#                     return action, None
#                 position = int(input("choose target: "))
#                 targeting = self.get_target_input(position)
#                 return action, targeting
#             except Exception as e:
#                 print(e)
#                 continue
