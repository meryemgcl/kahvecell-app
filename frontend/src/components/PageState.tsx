type PageStateProps =
  | {
      type: 'loading'
      message?: string
    }
  | {
      type: 'error'
      message: string
      onRetry: () => void
    }
  | {
      type: 'empty'
      title: string
      message: string
      actionLabel?: string
      onAction?: () => void
    }

export default function PageState(props: PageStateProps) {
  if (props.type === 'loading') {
    return (
      <section className="page-state page-state-loading" role="status" aria-live="polite">
        <span className="loading-spinner" aria-hidden="true"></span>
        <p>{props.message || 'Yükleniyor...'}</p>
      </section>
    )
  }

  if (props.type === 'error') {
    return (
      <section className="page-state page-state-error" role="alert">
        <span className="state-icon" aria-hidden="true">!</span>
        <h2>Bir şeyler ters gitti</h2>
        <p>{props.message}</p>
        <button type="button" onClick={props.onRetry}>Tekrar Dene</button>
      </section>
    )
  }

  return (
    <section className="page-state page-state-empty" role="status">
      <span className="state-icon state-icon-empty" aria-hidden="true">☕</span>
      <h2>{props.title}</h2>
      <p>{props.message}</p>
      {props.actionLabel && props.onAction && (
        <button type="button" onClick={props.onAction}>{props.actionLabel}</button>
      )}
    </section>
  )
}
