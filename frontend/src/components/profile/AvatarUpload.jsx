import { useRef, useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { uploadAvatar, deleteAvatar } from '../../api/users'
import Avatar from '../ui/Avatar'

export default function AvatarUpload() {
  const { user, refreshUser } = useAuth()
  const inputRef = useRef(null)
  const [preview, setPreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPreview(URL.createObjectURL(file))
    setUploading(true)
    setError('')
    try {
      const { data } = await uploadAvatar(file)
      refreshUser(data)
      setPreview(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.')
      setPreview(null)
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const handleRemove = async () => {
    if (!window.confirm('Remove your profile picture?')) return
    try {
      const { data } = await deleteAvatar()
      refreshUser(data)
    } catch {
      setError('Failed to remove photo.')
    }
  }

  const displayUser = preview
    ? { ...user, profile_picture_path: null, _preview: preview }
    : user

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Preview or current avatar */}
      <div className="relative">
        {preview ? (
          <img src={preview} alt="Preview" className="w-24 h-24 rounded-full object-cover ring-4 ring-brand-100" />
        ) : (
          <Avatar user={user} size="lg" />
        )}
        {uploading && (
          <div className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        )}
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={uploading}
          className="text-sm bg-brand-600 text-white px-4 py-1.5 rounded-full hover:bg-brand-700 disabled:opacity-60 transition"
        >
          {user?.profile_picture_path ? 'Change Photo' : 'Upload Photo'}
        </button>
        {user?.profile_picture_path && (
          <button
            type="button"
            onClick={handleRemove}
            className="text-sm border border-gray-300 text-gray-600 px-4 py-1.5 rounded-full hover:bg-gray-50 transition"
          >
            Remove
          </button>
        )}
      </div>
      <p className="text-xs text-gray-400">JPEG, PNG or WebP · max 5 MB</p>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  )
}
