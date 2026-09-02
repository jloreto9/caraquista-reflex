import reflex as rx

config = rx.Config(
    app_name="republicaraquistapp",
    cors_allowed_origins=["*"],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="dark",
                has_background=True,
                accent_color="amber",
                gray_color="slate",
                radius="large",
            )
        ),
    ]
)