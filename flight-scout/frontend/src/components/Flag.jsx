// Country flag image via flagcdn.com
export default function Flag({ cc, size = 16, style = {} }) {
  if (!cc) return null;
  return (
    <img
      src={`https://flagcdn.com/w40/${cc}.png`}
      alt=""
      width={size}
      height={Math.round(size * 0.75)}
      style={{ borderRadius: 2, verticalAlign: 'middle', ...style }}
    />
  );
}
