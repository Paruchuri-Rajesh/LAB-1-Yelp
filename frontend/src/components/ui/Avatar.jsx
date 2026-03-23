import { getAvatarUrl, getInitials } from '../../utils/formatters'

const COLORS = [
  'bg-red-400', 'bg-orange-400', 'bg-amber-400', 'bg-green-500',
  'bg-teal-500', 'bg-blue-500', 'bg-indigo-500', 'bg-purple-500',
]

function colorFromName(name = '') {
  const idx = name.charCodeAt(0) % COLORS.length
  return COLORS[idx] || COLORS[0]
}

const sizeClasses = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-sm', lg: 'w-16 h-16 text-xl' }

export default function Avatar({ user, size = 'md' }) {
  const avatarUrl = getAvatarUrl(user?.profile_picture_path)
  const initials = getInitials(user?.name)
  const sz = sizeClasses[size] || sizeClasses.md

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={user?.name}
        className={`${sz} rounded-full object-cover ring-2 ring-white`}
      />
    )
  }
  return (
    <div className={`${sz} ${colorFromName(user?.name)} rounded-full flex items-center justify-center text-white font-semibold ring-2 ring-white`}>
      {initials || '?'}
    </div>
  )
}
