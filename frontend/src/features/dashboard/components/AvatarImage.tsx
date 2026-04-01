import { useEffect, useState } from 'react';

type AvatarImageProps = {
  src: string | null;
  alt: string;
  fallbackText: string;
  imageClassName: string;
  fallbackClassName: string;
};

export function AvatarImage({
  src,
  alt,
  fallbackText,
  imageClassName,
  fallbackClassName,
}: AvatarImageProps) {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setHasError(false);
  }, [src]);

  if (!src || hasError) {
    return <div className={fallbackClassName}>{fallbackText}</div>;
  }

  return (
    <img
      className={imageClassName}
      src={src}
      alt={alt}
      onError={() => setHasError(true)}
    />
  );
}
