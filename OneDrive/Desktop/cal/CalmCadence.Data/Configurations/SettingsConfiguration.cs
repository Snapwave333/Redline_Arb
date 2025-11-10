using CalmCadence.Core.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace CalmCadence.Data.Configurations;

public class SettingsConfiguration : IEntityTypeConfiguration<Settings>
{
    public void Configure(EntityTypeBuilder<Settings> builder)
    {
        builder.ToTable("Settings");
        builder.HasKey(s => s.Id);

        builder.Property(s => s.TimeZone).IsRequired().HasMaxLength(200);
        builder.Property(s => s.CreatedAt).IsRequired();
        builder.Property(s => s.UpdatedAt).IsRequired();

        builder.HasIndex(s => s.FirstDayOfWeek);
    }
}
