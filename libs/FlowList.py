
class FlowList(list):
    def __init__(self, *args):
        super().__init__(*args)
        self._backup = list(self)  # keep a copy of original data

    def remove_by_id(self, target_id):
        """Remove a tuple by its ID (second element)."""
        for item in self[:]:
            if item[1] == target_id:
                self.remove(item)
                break

    def restore_by_id(self, target_id):
        """Restore a previously removed tuple by its ID."""
        for item in self._backup:
            if item[1] == target_id and item not in self:
                self.append(item)
                break

    def restore_all(self):
        """Restore all items from backup if missing."""
        for item in self._backup:
            if item not in self:
                self.append(item)

