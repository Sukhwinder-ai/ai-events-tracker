export default function BackgroundVideo() {
  return (
    <div className="bg-video-wrap" aria-hidden="true">
      <video
        className="bg-video"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
      >
        <source src="/background.mp4" type="video/mp4" />
      </video>
      <div className="bg-scrim" />
    </div>
  );
}
