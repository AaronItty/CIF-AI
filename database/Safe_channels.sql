create view safe_channels as
select
  id,
  organization_id,
  type,
  display_name,
  status,
  last_error,
  last_active_at,
  connected_at
from channels;